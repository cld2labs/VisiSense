import Badge from '../ui/Badge';

export default function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-bg-secondary bg-opacity-80 backdrop-blur border-b border-border-subtle">
      <div className="container mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img
              src="https://cloud2labs.com/wp-content/uploads/2024/09/Cloud2labs-logo.png"
              alt="Cloud2 Labs"
              className="h-8"
            />
            <div className="w-px h-8 bg-border-subtle" />
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold gradient-text">VisiSense</h1>
              <span className="text-text-muted">— CatalogIQ</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <Badge variant="cyan" size="sm">
              Powered by Local Vision Model Inference
            </Badge>
          </div>
        </div>
      </div>
    </nav>
  );
}
