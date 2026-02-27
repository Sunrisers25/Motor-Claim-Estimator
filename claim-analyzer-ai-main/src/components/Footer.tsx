import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background/50">
      <div className="container py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-bold text-foreground text-lg mb-2">🚗 Motor Claim AI</h3>
            <p className="text-sm text-muted-foreground">
              AI-powered motor insurance claim estimator. Built for KL University Hackathon.
            </p>
          </div>
          <div>
            <h4 className="font-semibold text-foreground mb-2">Quick Links</h4>
            <div className="flex flex-col gap-1">
              <Link to="/" className="text-sm text-muted-foreground hover:text-primary transition-colors">Home</Link>
              <Link to="/claim" className="text-sm text-muted-foreground hover:text-primary transition-colors">Start Claim</Link>
              <Link to="/analytics" className="text-sm text-muted-foreground hover:text-primary transition-colors">Analytics</Link>
            </div>
          </div>
          <div>
            <h4 className="font-semibold text-foreground mb-2">Project</h4>
            <p className="text-sm text-muted-foreground">KL University Hackathon</p>
            <a href="#" className="text-sm text-primary hover:underline">GitHub Repository →</a>
          </div>
        </div>
        <div className="mt-8 pt-6 border-t border-border text-center text-xs text-muted-foreground">
          © 2025 Motor Claim AI. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
