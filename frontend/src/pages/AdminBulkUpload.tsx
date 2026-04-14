import { useState } from 'react';
import { UploadCloud, FileType, CheckCircle2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { API_URL } from '@/api/client';
import { toast } from 'sonner';

export default function AdminBulkUpload() {
  const [dragActive, setDragActive] = useState(false);
  const [zipFile, setZipFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.zip')) {
        setZipFile(file);
      } else {
        toast.error("Please upload a .zip file containing your CSV and images.");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setZipFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!zipFile) return;
    setUploading(true);
    const token = localStorage.getItem('token');
    
    const formData = new FormData();
    formData.append("file", zipFile);

    try {
      const res = await fetch(`${API_URL}/products/bulk/zip`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData
      });
      const data = await res.json();
      
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      
      toast.success(`Successfully added ${data.created} products!`);
      if (data.errors && data.errors.length > 0) {
        toast.error(`There were ${data.errors.length} row errors. Check logs.`);
      }
      setZipFile(null);
    } catch (err: any) {
      toast.error(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-primary">Bulk Upload</h1>
        <p className="text-muted-foreground">Quickly add multiple items via ZIP archive or Drag and Drop.</p>
      </div>

      <div className="grid md:grid-cols-2 gap-8">
        
        {/* ZIP Upload Section */}
        <div className="bg-muted/30 p-6 rounded-xl border border-border">
          <h2 className="text-lg font-semibold mb-2">ZIP File Upload</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Upload a .zip file containing a <span className="font-mono text-primary bg-primary/10 px-1 rounded">products.csv</span> and all associated image files.
          </p>

          <div
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${dragActive ? 'border-primary bg-primary/5' : 'border-border bg-card'} ${zipFile ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {zipFile ? (
              <div className="space-y-3">
                <div className="mx-auto w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center text-emerald-600">
                  <CheckCircle2 size={24} />
                </div>
                <p className="font-medium text-emerald-700 dark:text-emerald-400">{zipFile.name}</p>
                <p className="text-xs text-muted-foreground">{(zipFile.size / 1024 / 1024).toFixed(2)} MB</p>
                <Button 
                  onClick={handleUpload} 
                  disabled={uploading} 
                  className="w-full mt-4 bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {uploading ? "Extracting & Uploading..." : "Process ZIP Archive"}
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setZipFile(null)} disabled={uploading}>
                  Cancel
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center text-primary">
                  <FileType size={24} />
                </div>
                <div>
                  <p className="font-medium">Drag & drop your .zip file here</p>
                  <p className="text-xs text-muted-foreground mt-1">or click to browse</p>
                </div>
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleFileChange}
                  className="hidden"
                  id="zip-upload"
                />
                <Button asChild variant="outline" className="mt-2">
                  <label htmlFor="zip-upload" className="cursor-pointer">
                    Select ZIP File
                  </label>
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* Visual Workflow Section (Coming Soon/Placeholder) */}
        <div className="bg-muted/30 p-6 rounded-xl border border-border flex flex-col items-center justify-center text-center opacity-70">
          <UploadCloud size={48} className="text-muted-foreground mb-4" />
          <h2 className="text-lg font-semibold mb-2">Visual Drag & Drop</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Drag images directly to the browser to visually create products row by row.
          </p>
          <div className="bg-primary/10 text-primary px-3 py-1 rounded-full text-xs font-semibold">
            In Development
          </div>
        </div>

      </div>
    </div>
  );
}
