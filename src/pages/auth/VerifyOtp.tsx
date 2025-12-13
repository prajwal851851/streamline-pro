import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "@/hooks/use-toast";

const VerifyOtp = () => {
  const { state } = useLocation() as any;
  const { verifyOtp, requestOtp } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState(state?.email || "");
  const [code, setCode] = useState("");
  const [purpose, setPurpose] = useState<"verify" | "reset">(state?.purpose || "verify");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const resp = await verifyOtp(email, code, purpose);
      if ((resp as any).token) {
        toast({ title: "Verified!" });
        navigate("/");
      } else {
        toast({ title: "Verified", description: (resp as any).detail || "Success" });
        if (purpose === "reset") navigate("/auth/login");
      }
    } catch (error: any) {
      toast({ title: "Verification failed", description: error.message || "Invalid code", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const resend = async () => {
    try {
      await requestOtp(email, purpose);
      toast({ title: "OTP resent" });
    } catch (error: any) {
      toast({ title: "Could not resend", description: error.message, variant: "destructive" });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-background px-4">
      <Card className="w-full max-w-md shadow-xl border-primary/20">
        <CardHeader>
          <CardTitle>Verify code</CardTitle>
          <CardDescription>Enter the 6-digit code sent to your email.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit}>
            <div>
              <label className="text-sm text-muted-foreground">Email</label>
              <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Code</label>
              <Input required maxLength={6} value={code} onChange={(e) => setCode(e.target.value)} />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Verifying..." : "Verify"}
            </Button>
          </form>
          <div className="mt-4 text-sm text-muted-foreground flex items-center justify-between">
            <span>Didn&apos;t get it?</span>
            <Button variant="link" onClick={resend} className="px-0">
              Resend OTP
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default VerifyOtp;

