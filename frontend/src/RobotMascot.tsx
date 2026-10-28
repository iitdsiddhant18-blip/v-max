import { Component, Suspense, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import type { Group, Mesh } from "three";

interface PointerState {
  x: number;
  y: number;
}

function RobotCharacter({ pointer, reducedMotion }: { pointer: PointerState; reducedMotion: boolean }) {
  const headRef = useRef<Group>(null);
  const bodyRef = useRef<Group>(null);
  const leftEyeRef = useRef<Mesh>(null);
  const rightEyeRef = useRef<Mesh>(null);

  useFrame(({ clock }, delta) => {
    const elapsed = clock.getElapsedTime();
    const smooth = Math.min(1, delta * 5);

    // Target rotations clamped to safe physical limits
    // Yaw: +/- 0.42 rad (~24 deg), Pitch: +/- 0.22 rad (~13 deg)
    const targetYaw = reducedMotion ? 0 : Math.max(-0.45, Math.min(0.45, pointer.x * 0.42));
    const targetPitch = reducedMotion ? 0 : Math.max(-0.25, Math.min(0.25, -pointer.y * 0.22));

    if (headRef.current) {
      headRef.current.rotation.y += (targetYaw - headRef.current.rotation.y) * smooth;
      headRef.current.rotation.x += (targetPitch - headRef.current.rotation.x) * smooth;
      
      // Subtle idle breathing motion
      const breath = reducedMotion ? 0 : Math.sin(elapsed * 1.6) * 0.025;
      headRef.current.position.y = 0.42 + breath;
    }

    if (bodyRef.current) {
      const bodyBreath = reducedMotion ? 0 : Math.sin(elapsed * 1.6) * 0.015;
      bodyRef.current.position.y = -0.32 + bodyBreath;
    }

    // Eye pupils subtle tracking inside visor
    if (leftEyeRef.current && rightEyeRef.current && !reducedMotion) {
      const pupilShiftX = pointer.x * 0.035;
      const pupilShiftY = -pointer.y * 0.025;
      leftEyeRef.current.position.x = -0.30 + pupilShiftX;
      leftEyeRef.current.position.y = 0.06 + pupilShiftY;
      rightEyeRef.current.position.x = 0.30 + pupilShiftX;
      rightEyeRef.current.position.y = 0.06 + pupilShiftY;
    }
  });

  return (
    <group position={[0, -0.15, 0]}>
      {/* 1. Floor Books Stack (Base under feet) */}
      <group position={[0, -1.35, 0]}>
        {/* Soft ground contact shadow */}
        <mesh position={[0, -0.18, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[2.8, 2.2]} />
          <meshBasicMaterial color="#bfa15c" opacity={0.25} transparent />
        </mesh>
        
        {/* Bottom large book */}
        <mesh position={[0, -0.09, 0]} castShadow receiveShadow>
          <boxGeometry args={[1.9, 0.16, 1.4]} />
          <meshStandardMaterial color="#4a5568" roughness={0.6} />
        </mesh>
        <mesh position={[0, -0.09, 0.04]}>
          <boxGeometry args={[1.82, 0.13, 1.34]} />
          <meshStandardMaterial color="#f7fafc" roughness={0.9} />
        </mesh>

        {/* Second floor book, slightly rotated */}
        <group rotation={[0, 0.14, 0]} position={[0.08, 0.08, 0]}>
          <mesh castShadow receiveShadow>
            <boxGeometry args={[1.7, 0.15, 1.3]} />
            <meshStandardMaterial color="#718096" roughness={0.5} />
          </mesh>
          <mesh position={[0, 0, 0.03]}>
            <boxGeometry args={[1.64, 0.12, 1.24]} />
            <meshStandardMaterial color="#edf2f7" roughness={0.9} />
          </mesh>
        </group>
      </group>

      {/* 2. Feet and Legs */}
      <group position={[0, -1.18, 0]}>
        {/* Left Foot */}
        <mesh position={[-0.38, 0, 0.08]} castShadow>
          <boxGeometry args={[0.34, 0.18, 0.52]} />
          <meshStandardMaterial color="#f5bc28" metalness={0.15} roughness={0.35} />
        </mesh>
        <mesh position={[-0.38, 0.14, -0.02]}>
          <cylinderGeometry args={[0.13, 0.15, 0.18, 16]} />
          <meshStandardMaterial color="#2d3748" metalness={0.4} roughness={0.4} />
        </mesh>

        {/* Right Foot */}
        <mesh position={[0.38, 0, 0.08]} castShadow>
          <boxGeometry args={[0.34, 0.18, 0.52]} />
          <meshStandardMaterial color="#f5bc28" metalness={0.15} roughness={0.35} />
        </mesh>
        <mesh position={[0.38, 0.14, -0.02]}>
          <cylinderGeometry args={[0.13, 0.15, 0.18, 16]} />
          <meshStandardMaterial color="#2d3748" metalness={0.4} roughness={0.4} />
        </mesh>
      </group>

      {/* 3. Anchored Torso & Held Books Stack */}
      <group ref={bodyRef} position={[0, -0.32, 0]}>
        {/* Rounded Yellow Torso */}
        <mesh position={[0, -0.22, 0]} castShadow>
          <capsuleGeometry args={[0.62, 0.54, 16, 24]} />
          <meshStandardMaterial color="#f6c63c" metalness={0.12} roughness={0.32} />
        </mesh>

        {/* White chest plate / badge */}
        <mesh position={[0, -0.08, 0.55]}>
          <boxGeometry args={[0.55, 0.28, 0.1]} />
          <meshStandardMaterial color="#ffffff" metalness={0.05} roughness={0.2} />
        </mesh>
        {/* Cyan power line on chest */}
        <mesh position={[0, -0.08, 0.61]}>
          <boxGeometry args={[0.42, 0.06, 0.02]} />
          <meshStandardMaterial color="#38bdf8" emissive="#38bdf8" emissiveIntensity={0.6} />
        </mesh>

        {/* Arms holding the book stack */}
        {/* Left Arm */}
        <group position={[-0.72, -0.15, 0.15]} rotation={[0.4, 0.3, -0.25]}>
          <mesh castShadow>
            <capsuleGeometry args={[0.15, 0.48, 8, 16]} />
            <meshStandardMaterial color="#f6c63c" roughness={0.35} />
          </mesh>
          {/* Hand clasping book */}
          <mesh position={[0.05, -0.28, 0.2]}>
            <sphereGeometry args={[0.13, 16, 16]} />
            <meshStandardMaterial color="#334155" metalness={0.3} roughness={0.3} />
          </mesh>
        </group>

        {/* Right Arm */}
        <group position={[0.72, -0.15, 0.15]} rotation={[0.4, -0.3, 0.25]}>
          <mesh castShadow>
            <capsuleGeometry args={[0.15, 0.48, 8, 16]} />
            <meshStandardMaterial color="#f6c63c" roughness={0.35} />
          </mesh>
          {/* Hand clasping book */}
          <mesh position={[-0.05, -0.28, 0.2]}>
            <sphereGeometry args={[0.13, 16, 16]} />
            <meshStandardMaterial color="#334155" metalness={0.3} roughness={0.3} />
          </mesh>
        </group>

        {/* Held Books Stack in front of torso */}
        <group position={[0, -0.34, 0.55]} rotation={[0.05, 0, 0]}>
          {/* Book 1 (Bottom, Red Spine) */}
          <mesh position={[0, -0.11, 0]} castShadow>
            <boxGeometry args={[1.12, 0.11, 0.85]} />
            <meshStandardMaterial color="#ef4444" roughness={0.4} />
          </mesh>
          <mesh position={[0, -0.11, 0.04]}>
            <boxGeometry args={[1.06, 0.08, 0.81]} />
            <meshStandardMaterial color="#fffbeb" roughness={0.8} />
          </mesh>

          {/* Book 2 (Middle, White with Teal Ribbon) */}
          <mesh position={[0, 0, 0.02]} castShadow>
            <boxGeometry args={[1.05, 0.11, 0.82]} />
            <meshStandardMaterial color="#f8fafc" roughness={0.3} />
          </mesh>
          <mesh position={[0.3, 0, 0.44]}>
            <boxGeometry args={[0.1, 0.12, 0.04]} />
            <meshStandardMaterial color="#0ea5e9" roughness={0.5} />
          </mesh>

          {/* Book 3 (Top, Vibrant Royal Blue) */}
          <mesh position={[0, 0.11, 0.04]} castShadow>
            <boxGeometry args={[0.98, 0.11, 0.78]} />
            <meshStandardMaterial color="#2563eb" roughness={0.35} />
          </mesh>
          <mesh position={[0, 0.11, 0.08]}>
            <boxGeometry args={[0.92, 0.08, 0.74]} />
            <meshStandardMaterial color="#ffffff" roughness={0.8} />
          </mesh>
        </group>
      </group>

      {/* 4. Independently Pivoting Head Group */}
      <group ref={headRef} position={[0, 0.42, 0.08]}>
        {/* Neck collar connector */}
        <mesh position={[0, -0.45, 0]}>
          <cylinderGeometry args={[0.26, 0.32, 0.22, 24]} />
          <meshStandardMaterial color="#334155" metalness={0.5} roughness={0.3} />
        </mesh>

        {/* Main Yellow Helmet */}
        <mesh castShadow>
          <sphereGeometry args={[1.05, 48, 36]} />
          <meshStandardMaterial color="#f6c63c" metalness={0.14} roughness={0.28} />
        </mesh>

        {/* Top Antenna */}
        <mesh position={[0, 1.15, -0.05]} rotation={[-0.1, 0, 0]}>
          <cylinderGeometry args={[0.038, 0.038, 0.38, 16]} />
          <meshStandardMaterial color="#e5a821" metalness={0.6} roughness={0.2} />
        </mesh>
        <mesh position={[0, 1.40, -0.08]}>
          <sphereGeometry args={[0.15, 24, 20]} />
          <meshStandardMaterial color="#f6c63c" emissive="#f6c63c" emissiveIntensity={0.3} metalness={0.2} roughness={0.2} />
        </mesh>

        {/* Blue Ear-Cup Dials (Left & Right) */}
        {[-1, 1].map((side) => (
          <group key={side} position={[side * 1.02, 0.02, 0]} rotation={[0, 0, side * -Math.PI / 2]}>
            {/* Outer Ear Rim */}
            <mesh>
              <cylinderGeometry args={[0.34, 0.34, 0.16, 32]} />
              <meshStandardMaterial color="#38bdf8" metalness={0.25} roughness={0.3} />
            </mesh>
            {/* Inner Ear Core */}
            <mesh position={[0, 0.09, 0]}>
              <cylinderGeometry args={[0.22, 0.22, 0.08, 24]} />
              <meshStandardMaterial color="#0284c7" metalness={0.4} roughness={0.2} />
            </mesh>
          </group>
        ))}

        {/* Glossy Dark Visor / Faceplate */}
        <mesh position={[0, 0.02, 0.62]} scale={[0.82, 0.54, 0.46]}>
          <sphereGeometry args={[1, 40, 28]} />
          <meshStandardMaterial color="#0f172a" metalness={0.35} roughness={0.12} />
        </mesh>

        {/* Giant Expressive Eyes */}
        {/* Left Eye */}
        <group position={[-0.30, 0.06, 0.98]}>
          {/* Eye Socket Sclera */}
          <mesh scale={[0.22, 0.28, 0.06]}>
            <sphereGeometry args={[1, 24, 20]} />
            <meshStandardMaterial color="#38bdf8" emissive="#38bdf8" emissiveIntensity={0.6} />
          </mesh>
          {/* Pupil */}
          <mesh ref={leftEyeRef} position={[0, 0, 0.04]} scale={[0.13, 0.18, 0.04]}>
            <sphereGeometry args={[1, 20, 16]} />
            <meshBasicMaterial color="#090d16" />
          </mesh>
          {/* Specular Catchlight Sparkle */}
          <mesh position={[-0.05, 0.08, 0.06]} scale={[0.045, 0.045, 0.02]}>
            <sphereGeometry args={[1, 12, 10]} />
            <meshBasicMaterial color="#ffffff" />
          </mesh>
        </group>

        {/* Right Eye */}
        <group position={[0.30, 0.06, 0.98]}>
          {/* Eye Socket Sclera */}
          <mesh scale={[0.22, 0.28, 0.06]}>
            <sphereGeometry args={[1, 24, 20]} />
            <meshStandardMaterial color="#38bdf8" emissive="#38bdf8" emissiveIntensity={0.6} />
          </mesh>
          {/* Pupil */}
          <mesh ref={rightEyeRef} position={[0, 0, 0.04]} scale={[0.13, 0.18, 0.04]}>
            <sphereGeometry args={[1, 20, 16]} />
            <meshBasicMaterial color="#090d16" />
          </mesh>
          {/* Specular Catchlight Sparkle */}
          <mesh position={[-0.05, 0.08, 0.06]} scale={[0.045, 0.045, 0.02]}>
            <sphereGeometry args={[1, 12, 10]} />
            <meshBasicMaterial color="#ffffff" />
          </mesh>
        </group>

        {/* Cute rosy cheek accents */}
        {[-0.52, 0.52].map((x) => (
          <mesh key={x} position={[x, -0.16, 0.84]} scale={[0.11, 0.06, 0.02]}>
            <sphereGeometry args={[1, 14, 10]} />
            <meshBasicMaterial color="#f472b6" opacity={0.5} transparent />
          </mesh>
        ))}
      </group>
    </group>
  );
}

class WebGLErrorBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? <StaticRobot /> : this.props.children;
  }
}

export function StaticRobot() {
  return (
    <div className="blu-robot-fallback" role="img" aria-label="Blu friendly yellow mascot robot">
      <div className="blu-fallback-glow" />
      <div className="blu-fallback-antenna">
        <span className="blu-fallback-sphere" />
        <span className="blu-fallback-stem" />
      </div>
      <div className="blu-fallback-head">
        <div className="blu-fallback-ear left" />
        <div className="blu-fallback-visor">
          <div className="blu-fallback-eye left">
            <span className="blu-fallback-pupil" />
            <span className="blu-fallback-glint" />
          </div>
          <div className="blu-fallback-eye right">
            <span className="blu-fallback-pupil" />
            <span className="blu-fallback-glint" />
          </div>
        </div>
        <div className="blu-fallback-ear right" />
      </div>
      <div className="blu-fallback-body">
        <div className="blu-fallback-chest" />
        <div className="blu-fallback-books">
          <div className="blu-fallback-book blue" />
          <div className="blu-fallback-book white" />
          <div className="blu-fallback-book red" />
        </div>
      </div>
      <div className="blu-fallback-base-books">
        <div className="blu-fallback-floor-book gray" />
        <div className="blu-fallback-floor-book dark" />
      </div>
    </div>
  );
}

export default function RobotMascot() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [supported, setSupported] = useState(false);
  const [pointer, setPointer] = useState<PointerState>({ x: 0, y: 0 });
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    // Check WebGL availability safely
    try {
      const canvas = document.createElement("canvas");
      const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
      setSupported(Boolean(gl));
    } catch {
      setSupported(false);
    }

    // Check prefers-reduced-motion
    if (typeof window !== "undefined" && window.matchMedia) {
      const media = window.matchMedia("(prefers-reduced-motion: reduce)");
      setReducedMotion(media.matches);
      const listener = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
      media.addEventListener("change", listener);
      return () => media.removeEventListener("change", listener);
    }
  }, []);

  useEffect(() => {
    // Hero-wide pointer listener: computes normalized coordinates relative to robot head
    const handleMove = (event: MouseEvent) => {
      if (!containerRef.current || reducedMotion) return;
      const rect = containerRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height * 0.35; // approximate head position

      const dx = (event.clientX - centerX) / (window.innerWidth * 0.45);
      const dy = (event.clientY - centerY) / (window.innerHeight * 0.45);

      setPointer({
        x: Math.max(-1, Math.min(1, dx)),
        y: Math.max(-1, Math.min(1, dy)),
      });
    };

    const handleLeave = () => {
      setPointer({ x: 0, y: 0 });
    };

    // Attach to the closest hero section or window
    const heroEl = document.querySelector(".blu-hero") || window;
    heroEl.addEventListener("mousemove", handleMove as EventListener);
    heroEl.addEventListener("mouseleave", handleLeave as EventListener);
    window.addEventListener("blur", handleLeave);

    return () => {
      heroEl.removeEventListener("mousemove", handleMove as EventListener);
      heroEl.removeEventListener("mouseleave", handleLeave as EventListener);
      window.removeEventListener("blur", handleLeave);
    };
  }, [reducedMotion]);

  if (!supported) return <StaticRobot />;

  return (
    <div
      ref={containerRef}
      className="blu-robot-3d"
      aria-label="Interactive 3D Blu mascot robot tracking your cursor"
    >
      <WebGLErrorBoundary>
        <Suspense fallback={<StaticRobot />}>
          <Canvas
            camera={{ position: [0, 0.1, 4.4], fov: 42 }}
            dpr={[1, 1.5]}
            gl={{ antialias: true, alpha: true, powerPreference: "default" }}
            style={{ background: "transparent", width: "100%", height: "100%" }}
          >
            <ambientLight intensity={1.9} />
            <directionalLight position={[4, 6, 5]} intensity={2.6} castShadow />
            <directionalLight position={[-4, 3, 2]} intensity={1.1} color="#ffeaa7" />
            <pointLight position={[0, -1, 3]} intensity={0.9} color="#bae6fd" />
            <RobotCharacter pointer={pointer} reducedMotion={reducedMotion} />
          </Canvas>
        </Suspense>
      </WebGLErrorBoundary>
    </div>
  );
}
