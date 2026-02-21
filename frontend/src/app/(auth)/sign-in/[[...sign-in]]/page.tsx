import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-7xl items-center justify-center px-4 py-12 sm:px-6 lg:px-8">
      <SignIn />
    </div>
  );
}
