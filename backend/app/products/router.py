from typing import List, Optional
import os
import uuid
import shutil
import zipfile
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.products import models, schemas
from app.categories.models import Category
from app.auth.deps import get_current_admin_user
from app.auth.models import User
from app.database import get_db

router = APIRouter()

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

@router.get("/", response_model=List[schemas.ProductResponse])
async def read_products(
    skip: int = 0, 
    limit: int = 100, 
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(models.Product).where(models.Product.is_active == True)
    if category_id:
        query = query.where(models.Product.category_id == category_id)
    
    result = await db.execute(query.offset(skip).limit(limit))
    products = result.scalars().all()
    return products

@router.post("/", response_model=schemas.ProductResponse)
async def create_product(
    product: schemas.ProductCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.put("/{product_id}", response_model=schemas.ProductResponse)
async def update_product(
    product_id: int,
    product: schemas.ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(models.Product).where(models.Product.id == product_id, models.Product.is_active == True))
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    # Mask product instead of hard deleting
    result = await db.execute(select(models.Product).where(models.Product.id == product_id))
    db_product = result.scalars().first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db_product.is_active = False
    await db.commit()
    return {"ok": True, "masked": True}

# -----------------------------------------------------------------------------------
# BULK UPLOAD ENDPOINTS
# -----------------------------------------------------------------------------------

@router.post("/bulk/zip")
async def bulk_upload_zip(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Accepts a ZIP file containing products.csv and image files.
    Format of CSV: name,description,price,stock,category,image_filename
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Must be a .zip file")
        
    temp_zip_path = os.path.join(IMAGES_DIR, f"temp_{uuid.uuid4().hex}.zip")
    with open(temp_zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    extracted_count = 0
    errors = []
    
    try:
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            # Check for products.csv
            csv_files = [f for f in zip_ref.namelist() if f.endswith(".csv")]
            if not csv_files:
                raise HTTPException(status_code=400, detail="No CSV file found in the ZIP")
                
            csv_filename = csv_files[0]
            with zip_ref.open(csv_filename) as f:
                content = f.read().decode('utf-8')
                
            reader = csv.DictReader(io.StringIO(content))
            
            # Extract images and process rows
            for row in reader:
                try:
                    category_name = row.get("category", "").strip()
                    cat_id = None
                    if category_name:
                        # Find or create category
                        cat_res = await db.execute(select(Category).where(Category.name == category_name))
                        cat = cat_res.scalars().first()
                        if not cat:
                            slug = category_name.lower().replace(" ", "-")
                            cat = Category(name=category_name, slug=slug)
                            db.add(cat)
                            await db.commit()
                            await db.refresh(cat)
                        cat_id = cat.id

                    image_filename = row.get("image_filename", "").strip()
                    image_url = None
                    if image_filename and image_filename in zip_ref.namelist():
                        new_filename = f"{uuid.uuid4().hex}_{image_filename.replace(' ', '_')}"
                        target_path = os.path.join(IMAGES_DIR, new_filename)
                        
                        # Extract the specific file to our images dir
                        with zip_ref.open(image_filename) as zf, open(target_path, 'wb') as f_out:
                            shutil.copyfileobj(zf, f_out)
                        
                        image_url = f"/static/images/{new_filename}"

                    product = models.Product(
                        name=row.get("name", "").strip(),
                        description=row.get("description", "").strip(),
                        price=float(row.get("price", 0)),
                        stock=int(row.get("stock", 0)),
                        category_id=cat_id,
                        image_url=image_url
                    )
                    db.add(product)
                    extracted_count += 1
                except Exception as e:
                    errors.append(f"Row {row.get('name', 'Unknown')}: {str(e)}")
            
            await db.commit()
            
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
            
    return {"ok": True, "created": extracted_count, "errors": errors}

import json

@router.post("/bulk/visual")
async def bulk_upload_visual(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Accepts multipart/form-data.
    'products' field: stringified JSON array of product objects
    'files' field: array of files (matched by index mapped in the JSON, or sequentially)
    """
    form = await request.form()
    
    products_json = form.get("products")
    if not products_json:
        raise HTTPException(status_code=400, detail="Missing products JSON")
        
    try:
        products_data = json.loads(products_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
        
    created_count = 0
    errors = []
    
    for i, p_data in enumerate(products_data):
        try:
            category_name = p_data.get("category", "").strip()
            cat_id = None
            if category_name:
                # Find or create category
                cat_res = await db.execute(select(Category).where(Category.name == category_name))
                cat = cat_res.scalars().first()
                if not cat:
                    slug = category_name.lower().replace(" ", "-")
                    cat = Category(name=category_name, slug=slug)
                    db.add(cat)
                    await db.commit()
                    await db.refresh(cat)
                cat_id = cat.id

            # See if a file was uploaded for this product (matched by file_{index})
            file_field = form.get(f"file_{i}")
            image_url = None
            
            if file_field and hasattr(file_field, "filename") and file_field.filename:
                new_filename = f"{uuid.uuid4().hex}_{file_field.filename.replace(' ', '_')}"
                target_path = os.path.join(IMAGES_DIR, new_filename)
                
                with open(target_path, "wb") as buffer:
                    shutil.copyfileobj(file_field.file, buffer)
                    
                image_url = f"/static/images/{new_filename}"

            product = models.Product(
                name=p_data.get("name", "").strip(),
                description=p_data.get("description", "").strip(),
                price=float(p_data.get("price", 0)),
                stock=int(p_data.get("stock", 0)),
                category_id=cat_id,
                image_url=image_url
            )
            db.add(product)
            created_count += 1
            
        except Exception as e:
            errors.append(f"Item {i} ({p_data.get('name', 'Unknown')}): {str(e)}")
            
    await db.commit()
    return {"ok": True, "created": created_count, "errors": errors}
