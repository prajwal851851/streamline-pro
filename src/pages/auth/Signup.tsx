import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "@/hooks/use-toast";

const Signup = () => {
  const { signup, requestOtp } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", first_name: "", last_name: "" });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await signup(form);
      await requestOtp(form.email, "verify");
      toast({ title: "Account created", description: "Check your email for the OTP." });
      navigate("/auth/verify", { state: { email: form.email, purpose: "verify" } });
    } catch (error: any) {
      toast({ title: "Signup failed", description: error.message || "Try again.", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-background px-4">
      <Card className="w-full max-w-md shadow-xl border-primary/20">
        <CardHeader>
          <CardTitle>Create account</CardTitle>
          <CardDescription>Start streaming after email verification.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-muted-foreground">First name</label>
                <Input name="first_name" value={form.first_name} onChange={handleChange} />
              </div>
              <div>
                <label className="text-sm text-muted-foreground">Last name</label>
                <Input name="last_name" value={form.last_name} onChange={handleChange} />
              </div>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Email</label>
              <Input type="email" name="email" required value={form.email} onChange={handleChange} />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Password</label>
              <Input type="password" name="password" required value={form.password} onChange={handleChange} />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Creating..." : "Create account"}
            </Button>
          </form>
          <div className="mt-4 text-sm text-muted-foreground text-center">
            Already have an account?{" "}
            <Link to="/auth/login" className="hover:text-primary">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Signup;

