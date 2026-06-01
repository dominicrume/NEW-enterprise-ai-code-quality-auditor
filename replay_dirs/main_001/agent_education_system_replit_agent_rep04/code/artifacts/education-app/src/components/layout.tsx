import React from "react";
import { Link, useLocation } from "wouter";
import { Button } from "@/components/ui/button";
import { BookOpen, LogOut } from "lucide-react";

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const [, setLocation] = useLocation();
  const email = localStorage.getItem("auth_email");

  const handleLogout = () => {
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_email");
    setLocation("/login");
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/courses" className="flex items-center gap-2 text-primary font-medium hover:text-primary/90 transition-colors" data-testid="link-home">
            <BookOpen className="w-5 h-5" />
            <span>Agent Education</span>
          </Link>
          <div className="flex items-center gap-4">
            {email && <span className="text-sm text-muted-foreground hidden sm:inline-block" data-testid="text-user-email">{email}</span>}
            <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-2" data-testid="button-logout">
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </Button>
          </div>
        </div>
      </header>
      <main className="flex-1 container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  );
}
