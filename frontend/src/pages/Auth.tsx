import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { BookOpen, Mail, Lock, User, Eye, EyeOff, ArrowLeft } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWoodyButton } from "@/hooks/useWoodyButton";
import { useRegister, useLogin } from "@/hooks/useAuth";
import { useToast } from "@/hooks/use-toast";

export default function Auth() {
  const navigate = useNavigate();
  const { handleWoodyClick } = useWoodyButton();
  const { toast } = useToast();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const registerMutation = useRegister();
  const loginMutation = useLogin();

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.trim()) {
      newErrors.email = "Please enter your email address";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "Please enter a valid email address";
    }

    if (!formData.password) {
      newErrors.password = "Please enter your password";
    } else if (formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    if (mode === "register") {
      if (!formData.name.trim()) {
        newErrors.name = "Please enter your name";
      }
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = "Passwords do not match";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      if (mode === "register") {
        await registerMutation.mutateAsync({
          email: formData.email,
          password: formData.password,
          display_name: formData.name,
        });
      } else {
        await loginMutation.mutateAsync({
          email: formData.email,
          password: formData.password,
        });
      }
    } catch (error: any) {
      toast({
        variant: "destructive",
        title: mode === "register" ? "Registration failed" : "Login failed",
        description: error.message || "An error occurred. Please try again.",
      });
    }
  };

  const isLogin = mode === "login";

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-background">
      {/* Back to home link */}
      <Link
        to="/"
        className="absolute top-6 left-6 flex items-center gap-2 text-lg text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Home
      </Link>

      <div className="w-full max-w-md">
        <div className="bg-card border border-border rounded-xl p-10 shadow-sm">
          {/* Logo */}
          <div className="flex flex-col items-center mb-10">
            <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mb-5">
              <BookOpen className="w-8 h-8 text-primary" />
            </div>
            <h1 className="text-2xl font-project font-semibold text-foreground">Life Story</h1>
            <p className="text-lg text-muted-foreground mt-2 text-center">
              {isLogin ? "Welcome back!" : "Create your account"}
            </p>
          </div>

          {/* Mode Toggle */}
          <div className="flex bg-secondary rounded-lg p-1 mb-8">
            <button
              onClick={() => setMode("login")}
              className={cn(
                "flex-1 py-3 px-4 rounded-md text-lg font-medium transition-colors",
                isLogin ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              )}
            >
              Sign In
            </button>
            <button
              onClick={() => setMode("register")}
              className={cn(
                "flex-1 py-3 px-4 rounded-md text-lg font-medium transition-colors",
                !isLogin ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
              )}
            >
              Sign Up
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Name field (register only) */}
            {!isLogin && (
              <div className="space-y-2">
                <label className="text-lg font-medium text-foreground">Your Name</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Enter your full name"
                    className={cn(
                      "w-full pl-12 pr-4 py-4 rounded-lg bg-background border text-lg",
                      "text-foreground placeholder:text-muted-foreground",
                      "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary",
                      "transition-all",
                      errors.name ? "border-destructive" : "border-border"
                    )}
                  />
                </div>
                {errors.name && <p className="text-base text-destructive">{errors.name}</p>}
              </div>
            )}

            {/* Email field */}
            <div className="space-y-2">
              <label className="text-lg font-medium text-foreground">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="you@example.com"
                  className={cn(
                    "w-full pl-12 pr-4 py-4 rounded-lg bg-background border text-lg",
                    "text-foreground placeholder:text-muted-foreground",
                    "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary",
                    "transition-all",
                    errors.email ? "border-destructive" : "border-border"
                  )}
                />
              </div>
              {errors.email && <p className="text-base text-destructive">{errors.email}</p>}
            </div>

            {/* Password field */}
            <div className="space-y-2">
              <label className="text-lg font-medium text-foreground">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  placeholder="Enter your password"
                  className={cn(
                    "w-full pl-12 pr-14 py-4 rounded-lg bg-background border text-lg",
                    "text-foreground placeholder:text-muted-foreground",
                    "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary",
                    "transition-all",
                    errors.password ? "border-destructive" : "border-border"
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors p-1"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
              {errors.password && <p className="text-base text-destructive">{errors.password}</p>}
            </div>

            {/* Confirm Password field (register only) */}
            {!isLogin && (
              <div className="space-y-2">
                <label className="text-lg font-medium text-foreground">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <input
                    type={showPassword ? "text" : "password"}
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    placeholder="Re-enter your password"
                    className={cn(
                      "w-full pl-12 pr-4 py-4 rounded-lg bg-background border text-lg",
                      "text-foreground placeholder:text-muted-foreground",
                      "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary",
                      "transition-all",
                      errors.confirmPassword ? "border-destructive" : "border-border"
                    )}
                  />
                </div>
                {errors.confirmPassword && <p className="text-base text-destructive">{errors.confirmPassword}</p>}
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              onClick={handleWoodyClick}
              disabled={registerMutation.isPending || loginMutation.isPending}
              className="btn-woody w-full py-4 rounded-lg font-medium text-xl text-white mt-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {registerMutation.isPending || loginMutation.isPending
                ? "Loading..."
                : isLogin
                  ? "Sign In"
                  : "Create Account"}
            </button>
          </form>

          {/* Help text */}
          <p className="text-center text-muted-foreground mt-8">
            Need help? <a href="#" className="text-primary hover:underline">Contact us</a>
          </p>
        </div>
      </div>
    </div>
  );
}
