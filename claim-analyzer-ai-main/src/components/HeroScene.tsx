import { useRef, useMemo, useEffect, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Float } from "@react-three/drei";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";

/** Shared mouse tracker — rotates entire scene towards cursor */
function MouseTracker({ children }: { children: React.ReactNode }) {
  const groupRef = useRef<THREE.Group>(null!);
  const mouse = useRef({ x: 0, y: 0 });
  const { viewport } = useThree();

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      mouse.current.x = (e.clientX / window.innerWidth) * 2 - 1;
      mouse.current.y = -(e.clientY / window.innerHeight) * 2 + 1;
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, []);

  useFrame(() => {
    if (!groupRef.current) return;
    groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, mouse.current.x * 0.15, 0.05);
    groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, mouse.current.y * 0.08, 0.05);
  });

  return <group ref={groupRef}>{children}</group>;
}

/** Scroll-reactive wrapper — moves objects based on scroll */
function ScrollReactor({ scrollY }: { scrollY: React.MutableRefObject<number> }) {
  const ref = useRef<THREE.Group>(null!);
  useFrame(() => {
    if (!ref.current) return;
    const s = scrollY.current;
    ref.current.position.y = -s * 2;
    ref.current.rotation.z = s * 0.1;
  });
  return <group ref={ref} />;
}

/** Hover-reactive mesh wrapper */
function HoverMesh({ children, position, hoverScale = 1.25 }: { children: React.ReactNode; position: [number, number, number]; hoverScale?: number }) {
  const ref = useRef<THREE.Group>(null!);
  const [hovered, setHovered] = useState(false);
  const target = useRef(1);
  const clickSpin = useRef(0);
  const clickPulse = useRef(0);

  useEffect(() => { target.current = hovered ? hoverScale : 1; }, [hovered, hoverScale]);

  const handleClick = () => {
    clickSpin.current = Math.PI * 2;
    clickPulse.current = 1;
  };

  useFrame((_, delta) => {
    if (!ref.current) return;

    // Hover scale
    const baseScale = hovered ? hoverScale : 1;
    // Click pulse: brief scale bump that decays
    clickPulse.current = THREE.MathUtils.lerp(clickPulse.current, 0, 0.08);
    const pulseScale = 1 + clickPulse.current * 0.3;
    const s = THREE.MathUtils.lerp(ref.current.scale.x, baseScale * pulseScale, 0.1);
    ref.current.scale.setScalar(s);

    // Click spin: fast Y rotation that decays
    if (clickSpin.current > 0.01) {
      const spinStep = clickSpin.current * 0.08;
      ref.current.rotation.y += spinStep;
      clickSpin.current = THREE.MathUtils.lerp(clickSpin.current, 0, 0.08);
    }
  });

  return (
    <group
      ref={ref}
      position={position}
      onPointerOver={() => setHovered(true)}
      onPointerOut={() => setHovered(false)}
      onClick={handleClick}
    >
      {children}
    </group>
  );
}

/** Shield */
function Shield3D({ color, speed = 0.4 }: { color: string; speed?: number }) {
  const ref = useRef<THREE.Group>(null!);
  useFrame((state) => {
    ref.current.rotation.y = state.clock.elapsedTime * speed;
  });

  const shape = useMemo(() => {
    const s = new THREE.Shape();
    s.moveTo(0, 0.7);
    s.quadraticCurveTo(0.55, 0.55, 0.55, 0);
    s.quadraticCurveTo(0.55, -0.45, 0, -0.7);
    s.quadraticCurveTo(-0.55, -0.45, -0.55, 0);
    s.quadraticCurveTo(-0.55, 0.55, 0, 0.7);
    return s;
  }, []);

  return (
    <group ref={ref} scale={0.8}>
      <mesh>
        <extrudeGeometry args={[shape, { depth: 0.15, bevelEnabled: true, bevelThickness: 0.03, bevelSize: 0.03, bevelSegments: 3 }]} />
        <meshStandardMaterial color={color} roughness={0.25} metalness={0.85} emissive={color} emissiveIntensity={0.45} />
      </mesh>
    </group>
  );
}

/** Clipboard */
function Clipboard3D({ color, speed = 0.3 }: { color: string; speed?: number }) {
  const ref = useRef<THREE.Group>(null!);
  useFrame((state) => {
    ref.current.rotation.y = state.clock.elapsedTime * speed * 0.5;
    ref.current.rotation.z = Math.sin(state.clock.elapsedTime * speed) * 0.1;
  });

  return (
    <group ref={ref} scale={0.5}>
      <mesh>
        <boxGeometry args={[1, 1.4, 0.08]} />
        <meshStandardMaterial color={color} roughness={0.3} metalness={0.7} emissive={color} emissiveIntensity={0.4} />
      </mesh>
      <mesh position={[0, 0.75, 0.05]}>
        <boxGeometry args={[0.35, 0.15, 0.06]} />
        <meshStandardMaterial color="#94a3b8" roughness={0.2} metalness={0.9} />
      </mesh>
      {[-0.15, 0, 0.15, 0.3].map((y, i) => (
        <mesh key={i} position={[0, -y, 0.05]}>
          <boxGeometry args={[0.6 - i * 0.08, 0.04, 0.01]} />
          <meshStandardMaterial color="#cbd5e1" roughness={0.5} metalness={0.3} />
        </mesh>
      ))}
    </group>
  );
}

/** Car */
function Car3D({ color, speed = 0.3 }: { color: string; speed?: number }) {
  const ref = useRef<THREE.Group>(null!);
  useFrame((state) => {
    ref.current.rotation.y = state.clock.elapsedTime * speed;
  });

  return (
    <group ref={ref} scale={0.6}>
      <mesh position={[0, 0.3, 0]}>
        <boxGeometry args={[2.4, 0.5, 1.1]} />
        <meshStandardMaterial color={color} roughness={0.25} metalness={0.85} emissive={color} emissiveIntensity={0.5} />
      </mesh>
      <mesh position={[0.1, 0.75, 0]}>
        <boxGeometry args={[1.3, 0.45, 0.95]} />
        <meshStandardMaterial color="#1e3a5f" roughness={0.1} metalness={0.9} transparent opacity={0.7} />
      </mesh>
      {[[-0.7, 0, 0.55], [-0.7, 0, -0.55], [0.7, 0, 0.55], [0.7, 0, -0.55]].map((pos, i) => (
        <mesh key={i} position={pos as [number, number, number]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.2, 0.2, 0.12, 16]} />
          <meshStandardMaterial color="#111" roughness={0.6} metalness={0.3} />
        </mesh>
      ))}
      {[[1.2, 0.35, 0.35], [1.2, 0.35, -0.35]].map((pos, i) => (
        <mesh key={`hl-${i}`} position={pos as [number, number, number]}>
          <sphereGeometry args={[0.08, 8, 8]} />
          <meshStandardMaterial color="#ffd700" emissive="#ffd700" emissiveIntensity={0.8} />
        </mesh>
      ))}
    </group>
  );
}

/** Coin */
function Coin3D({ color, speed = 0.5 }: { color: string; speed?: number }) {
  const ref = useRef<THREE.Mesh>(null!);
  useFrame((state) => {
    ref.current.rotation.y = state.clock.elapsedTime * speed;
    ref.current.rotation.x = Math.sin(state.clock.elapsedTime * speed * 0.8) * 0.3;
  });
  return (
    <mesh ref={ref}>
      <cylinderGeometry args={[0.4, 0.4, 0.08, 32]} />
      <meshStandardMaterial color={color} roughness={0.2} metalness={0.9} emissive={color} emissiveIntensity={0.55} />
    </mesh>
  );
}

function Particles() {
  const count = 80;
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 14;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 10;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 8;
    }
    return pos;
  }, []);

  const ref = useRef<THREE.Points>(null!);
  useFrame((state) => {
    ref.current.rotation.y = state.clock.elapsedTime * 0.02;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial size={0.025} color="#6d9fff" transparent opacity={0.5} sizeAttenuation />
    </points>
  );
}

/** Cinematic camera zoom-in on load */
function CameraIntro() {
  const { camera } = useThree();
  const progress = useRef(0);

  useEffect(() => {
    camera.position.set(0, 0.5, 12);
  }, [camera]);

  useFrame((_, delta) => {
    if (progress.current >= 1) return;
    progress.current = Math.min(progress.current + delta * 0.35, 1);
    const t = 1 - Math.pow(1 - progress.current, 3); // ease-out cubic
    camera.position.z = THREE.MathUtils.lerp(12, 6, t);
    camera.position.y = THREE.MathUtils.lerp(0.5, 0, t);
  });

  return null;
}

export default function HeroScene() {
  const scrollY = useRef(0);

  useEffect(() => {
    const onScroll = () => {
      scrollY.current = window.scrollY / window.innerHeight;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="absolute inset-0 z-0">
      <Canvas
        camera={{ position: [0, 0, 6], fov: 55 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: "transparent" }}
      >
        <ambientLight intensity={1.2} />
        <directionalLight position={[5, 5, 5]} intensity={2} color="#ffffff" />
        <directionalLight position={[-3, 3, -3]} intensity={1.2} color="#8b5cf6" />
        <directionalLight position={[0, -3, 5]} intensity={0.8} color="#60a5fa" />
        <pointLight position={[0, 3, 0]} intensity={1.5} color="#3b82f6" />
        <CameraIntro />

        <MouseTracker>
          {/* Cars — hover to enlarge */}
          <Float speed={1} rotationIntensity={0.1} floatIntensity={0.3}>
            <HoverMesh position={[-3, -0.5, -1]}>
              <Car3D color="#2563eb" speed={0.25} />
            </HoverMesh>
          </Float>
          <Float speed={0.8} rotationIntensity={0.1} floatIntensity={0.2}>
            <HoverMesh position={[3.5, 0.8, -3]}>
              <Car3D color="#dc2626" speed={-0.2} />
            </HoverMesh>
          </Float>

          {/* Shield */}
          <Float speed={1.2} rotationIntensity={0.2} floatIntensity={0.4}>
            <HoverMesh position={[-2.5, 1.2, -1.5]} hoverScale={1.3}>
              <Shield3D color="#2563eb" speed={0.35} />
            </HoverMesh>
          </Float>

          {/* Clipboard */}
          <Float speed={1} rotationIntensity={0.15} floatIntensity={0.3}>
            <HoverMesh position={[3, -0.8, -2]} hoverScale={1.3}>
              <Clipboard3D color="#1e3a5f" speed={0.3} />
            </HoverMesh>
          </Float>

          {/* Coin */}
          <Float speed={1.5} rotationIntensity={0.3} floatIntensity={0.5}>
            <HoverMesh position={[0, 2, -2.5]} hoverScale={1.4}>
              <Coin3D color="#d97706" speed={0.5} />
            </HoverMesh>
          </Float>

          <Particles />
          <gridHelper args={[20, 30, "#1e3a5f", "#1e3a5f"]} position={[0, -2.5, 0]} />
        </MouseTracker>

        <EffectComposer>
          <Bloom
            intensity={0.5}
            luminanceThreshold={0.6}
            luminanceSmoothing={0.9}
            mipmapBlur
          />
        </EffectComposer>
      </Canvas>
    </div>
  );
}
