import { useState } from "react";
import {
   useNavigate,
     useLocation,
     Link,
} from "react-router-dom";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";
import Input from "../../components/ui/Input";
import Button from "../../components/ui/Button";
import { useToast } from "../../components/ui/Toast";
import { useAuth } from "../../context/AuthContext";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const { showToast } = useToast();
const handleLogin = async () => {
  if (!email.trim()) {
    showToast("Email is required.", "warning");
    return;
  }

  if (!password.trim()) {
    showToast("Password is required.", "warning");
    return;
  }

  const success = await login({
    email,
    password,
    rememberMe: false,
  });

  if (!success) {
    showToast("Invalid email or password.", "error");
    return;
  }

  showToast(
    "Welcome back to MUHUZE!",
    "success"
  );

 const from =
  location.state?.from?.pathname || "/";

navigate(from, { replace: true });
};

  return (
    <section className="py-16">
      <Container>
        <div className="max-w-md mx-auto">

          <SectionTitle
            title="Login"
            subtitle="Welcome back to MUHUZE."
          />

          <div className="space-y-5 mt-8">

            <Input
              label="Email Address"
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />

            <Input
              label="Password"
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            <Button
              className="w-full"
              onClick={handleLogin}
            >
              Login
            </Button>
<Link
  to="/forgot-password"
  className="text-blue-600 hover:underline"
>
  Forgot Password?
</Link>
          </div>

        </div>
      </Container>
    </section>
  );
}