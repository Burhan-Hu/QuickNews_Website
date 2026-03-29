/**
 * Three.js 3D 地球组件
 * 包含地球模型、大气层、热力图标记和交互功能
 */

import React, { useRef, useMemo, useEffect, useState } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Stars, Html } from '@react-three/drei';
import * as THREE from 'three';
import { latLonToVector3, getHeatmapColor, countryCoords } from '../utils/countryCoords';

// 地球纹理 URL (使用 NASA Blue Marble 贴图)
const EARTH_TEXTURE_URL = 'https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg';
const EARTH_BUMP_URL = 'https://unpkg.com/three-globe/example/img/earth-topology.png';

/**
 * 地球球体组件
 */
function EarthSphere({ 
  onCountryClick, 
  heatmapData = {}, 
  selectedCountry, 
  mode = 'default',
  rotationSpeed = 0.001 
}) {
  const meshRef = useRef();
  const groupRef = useRef();
  const [hoveredCountry, setHoveredCountry] = useState(null);
  
  // 加载地球纹理
  const [earthMap, bumpMap] = useLoader(THREE.TextureLoader, [EARTH_TEXTURE_URL, EARTH_BUMP_URL]);
  
  // 地球材质配置
  const earthMaterial = useMemo(() => {
    return new THREE.MeshPhongMaterial({
      map: earthMap,
      bumpMap: bumpMap,
      bumpScale: 0.05,
      specular: new THREE.Color(0x333333),
      shininess: 5,
    });
  }, [earthMap, bumpMap]);
  
  // 自转动画
  useFrame((state, delta) => {
    if (groupRef.current && mode !== 'static') {
      groupRef.current.rotation.y += rotationSpeed;
    }
  });
  
  // 处理国家点击
  const handleCountryClick = (countryCode) => {
    if (onCountryClick && mode === 'heatmap') {
      onCountryClick(countryCode);
    }
  };
  
  return (
    <group ref={groupRef}>
      {/* 地球主体 */}
      <mesh ref={meshRef} material={earthMaterial}>
        <sphereGeometry args={[5, 64, 64]} />
      </mesh>
      
      {/* 大气层 */}
      <Atmosphere />
      
      {/* 热力图标记 */}
      {mode === 'heatmap' && Object.entries(heatmapData).map(([code, count]) => {
        const info = countryCoords[code];
        if (!info) return null;
        
        const pos = latLonToVector3(info.lat, info.lon, 5.05);
        const color = getHeatmapColor(count, 50);
        const isSelected = selectedCountry === code;
        const isHovered = hoveredCountry === code;
        
        return (
          <group key={code} position={[pos.x, pos.y, pos.z]}>
            {/* 热力点 */}
            <mesh
              onClick={() => handleCountryClick(code)}
              onPointerOver={() => setHoveredCountry(code)}
              onPointerOut={() => setHoveredCountry(null)}
            >
              <sphereGeometry args={[0.15 + (count / 100), 16, 16]} />
              <meshBasicMaterial 
                color={color} 
                transparent 
                opacity={isSelected ? 1 : 0.8}
              />
            </mesh>
            
            {/* 选中效果 - 脉冲环 */}
            {isSelected && <PulseRing />}
            
            {/* 悬停提示 */}
            {(isHovered || isSelected) && (
              <Html distanceFactor={10}>
                <div className="glass px-3 py-2 rounded-lg text-white text-sm whitespace-nowrap pointer-events-none">
                  <span className="mr-2">{info.emoji}</span>
                  <span className="font-medium">{info.name}</span>
                  <span className="ml-2 text-[#00d4ff]">{count} 条新闻</span>
                </div>
              </Html>
            )}
          </group>
        );
      })}
      
      {/* 选中国家的标记 */}
      {selectedCountry && countryCoords[selectedCountry] && (
        <CountryMarker countryCode={selectedCountry} />
      )}
    </group>
  );
}

/**
 * 大气层组件
 */
function Atmosphere() {
  const meshRef = useRef();
  
  const atmosphereMaterial = useMemo(() => {
    return new THREE.ShaderMaterial({
      transparent: true,
      side: THREE.BackSide,
      uniforms: {},
      vertexShader: `
        varying vec3 vNormal;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        varying vec3 vNormal;
        void main() {
          float intensity = pow(0.6 - dot(vNormal, vec3(0, 0, 1.0)), 2.0);
          gl_FragColor = vec4(0.0, 0.8, 1.0, 1.0) * intensity * 0.5;
        }
      `,
    });
  }, []);
  
  return (
    <mesh ref={meshRef} material={atmosphereMaterial} scale={[1.15, 1.15, 1.15]}>
      <sphereGeometry args={[5, 64, 64]} />
    </mesh>
  );
}

/**
 * 脉冲环动画组件
 */
function PulseRing() {
  const meshRef = useRef();
  
  useFrame((state) => {
    if (meshRef.current) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.3;
      meshRef.current.scale.set(scale, scale, scale);
      meshRef.current.material.opacity = 0.5 - (scale - 1) * 0.3;
    }
  });
  
  return (
    <mesh ref={meshRef}>
      <ringGeometry args={[0.3, 0.35, 32]} />
      <meshBasicMaterial color="#00d4ff" transparent opacity={0.5} side={THREE.DoubleSide} />
    </mesh>
  );
}

/**
 * 国家标记组件
 */
function CountryMarker({ countryCode }) {
  const meshRef = useRef();
  const info = countryCoords[countryCode];
  
  if (!info) return null;
  
  const pos = latLonToVector3(info.lat, info.lon, 5.2);
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 2;
    }
  });
  
  return (
    <group position={[pos.x, pos.y, pos.z]}>
      {/* 标记点 */}
      <mesh ref={meshRef}>
        <coneGeometry args={[0.1, 0.3, 8]} />
        <meshBasicMaterial color="#00d4ff" />
      </mesh>
      
      {/* 光晕 */}
      <mesh>
        <sphereGeometry args={[0.2, 16, 16]} />
        <meshBasicMaterial color="#00d4ff" transparent opacity={0.3} />
      </mesh>
    </group>
  );
}

/**
 * 星空背景组件
 */
function StarField() {
  const pointsRef = useRef();
  
  const [positions, colors] = useMemo(() => {
    const count = 3000;
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);
    
    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      
      // 随机球面位置
      const r = 50 + Math.random() * 50;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      
      positions[i3] = r * Math.sin(phi) * Math.cos(theta);
      positions[i3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      positions[i3 + 2] = r * Math.cos(phi);
      
      // 星星颜色 (偏蓝白色)
      const brightness = 0.5 + Math.random() * 0.5;
      colors[i3] = brightness * (0.9 + Math.random() * 0.1);
      colors[i3 + 1] = brightness * (0.9 + Math.random() * 0.1);
      colors[i3 + 2] = brightness;
    }
    
    return [positions, colors];
  }, []);
  
  useFrame((state) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y = state.clock.elapsedTime * 0.02;
    }
  });
  
  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={positions.length / 3}
          array={positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={colors.length / 3}
          array={colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.15}
        vertexColors
        transparent
        opacity={0.8}
        sizeAttenuation
      />
    </points>
  );
}

/**
 * 主地球 3D 组件
 */
export default function Earth3D({
  mode = 'default',
  onCountryClick,
  heatmapData = {},
  selectedCountry = null,
  rotationSpeed = 0.001,
  enableControls = true,
  cameraPosition = [0, 0, 15],
}) {
  // 阻止事件冒泡的处理函数
  const handlePointerDown = enableControls ? undefined : (e) => e.stopPropagation();
  const handleWheel = enableControls ? undefined : (e) => e.stopPropagation();

  return (
    <div className="w-full h-full">
      <Canvas
        camera={{ position: cameraPosition, fov: 45, makeDefault: true }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
        frameloop="always"
        onPointerDown={handlePointerDown}
        onWheel={handleWheel}
        resize={{ scroll: false, debounce: 0 }}
        dpr={[1, 1.5]}
      >
        {/* 环境光 */}
        <ambientLight intensity={0.3} />
        
        {/* 太阳光 (方向光) */}
        <directionalLight
          position={[10, 5, 5]}
          intensity={1.5}
          color="#ffffff"
        />
        
        {/* 补充光源 */}
        <pointLight position={[-10, -5, -5]} intensity={0.5} color="#00d4ff" />
        
        {/* 星空背景 */}
        <StarField />
        
        {/* 地球 */}
        <EarthSphere
          mode={mode}
          onCountryClick={onCountryClick}
          heatmapData={heatmapData}
          selectedCountry={selectedCountry}
          rotationSpeed={rotationSpeed}
        />
        
        {/* 轨道控制器 */}
        {enableControls && (
          <OrbitControls
            key="orbit-controls"
            enableZoom={true}
            enablePan={false}
            minDistance={8}
            maxDistance={30}
            autoRotate={false}
          />
        )}
      </Canvas>
    </div>
  );
}
