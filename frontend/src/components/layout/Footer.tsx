import { Lock } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-border-subtle bg-bg-secondary mt-auto">
      <div className="container mx-auto px-6 py-6">
        <div className="flex flex-col items-center gap-3 text-sm text-text-muted">
          <div className="flex items-center gap-2">
            <Lock size={14} />
            <span>Runs locally on CPU · No data leaves your environment</span>
          </div>
          <p className="text-center">
            VisiSense — CatalogIQ by Cloud2 Labs.
            All AI-generated content must be reviewed before publication.
          </p>
        </div>
      </div>
    </footer>
  );
}
