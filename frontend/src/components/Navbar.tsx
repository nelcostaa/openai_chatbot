import { Link } from "react-router-dom";
import { BookOpen } from "lucide-react";
import { useWoodyButton } from "@/hooks/useWoodyButton";

export default function Navbar() {
    const { handleWoodyClick } = useWoodyButton();

    return (
        <div className="fixed top-0 left-0 right-0 z-50 px-4 pt-3 md:px-6 md:pt-4">
            <nav className="max-w-6xl mx-auto bg-white/70 backdrop-blur-md border border-white/20 rounded-full shadow-lg shadow-black/5">
                <div className="px-4 md:px-6 h-14 flex items-center justify-between">
                    {/* Logo */}
                    <Link to="/" className="flex items-center gap-2 group">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#5C3D2E] to-[#4A2F1F] flex items-center justify-center transition-transform group-hover:scale-105">
                            <BookOpen className="w-4 h-4 text-white" />
                        </div>
                        <span className="text-base md:text-lg font-semibold text-[#5C3D2E] font-project hidden sm:inline">
                            Life Story
                        </span>
                    </Link>

                    {/* Navigation Links */}
                    <div className="flex items-center gap-2 md:gap-4">
                        <Link
                            to="/auth"
                            className="text-sm text-[#8B6F5C] hover:text-[#5C3D2E] transition-colors font-medium px-3 py-1.5"
                        >
                            Log In
                        </Link>
                        <Link to="/auth">
                            <button
                                onClick={handleWoodyClick}
                                className="btn-modern px-4 py-1.5 rounded-full text-sm font-medium text-white"
                            >
                                Start for Free
                            </button>
                        </Link>
                    </div>
                </div>
            </nav>
        </div>
    );
}
