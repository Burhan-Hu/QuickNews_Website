/**
 * 主页组件
 * 包含开场动画、时钟、3D地球和导航按钮
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate, useLocation } from 'react-router-dom';
import Earth3D from '../components/Earth3D';
import Clock from '../components/Clock';
import GlassButton from '../components/GlassButton';

export default function Home() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // 判断是否从内部页面返回
  const isFromInternal = location.state?.fromInternal === true;
  // 检查是否已看过开场动画
  const hasSeenIntro = sessionStorage.getItem('qk_has_seen_intro') === 'true';
  
  // 仅当不是从内部页面返回且未看过开场动画时，才显示开场动画
  const [showIntro, setShowIntro] = useState(!isFromInternal && !hasSeenIntro);
  const [showUI, setShowUI] = useState(isFromInternal || hasSeenIntro);
  
  // 开场动画序列
  useEffect(() => {
    // 如果不需要显示开场动画，直接返回
    if (!showIntro) {
      return;
    }
    
    const timer = setTimeout(() => {
      setShowIntro(false);
      setShowUI(true);
      // 动画播放结束后，标记已看过开场动画
      sessionStorage.setItem('qk_has_seen_intro', 'true');
    }, 4000);
    
    return () => clearTimeout(timer);
  }, [showIntro]);
  
  // 导航处理 - 跳转到其他页面时标记为内部导航
  const handleNavigate = (path) => {
    navigate(path, { state: { fromInternal: true } });
  };
  
  return (
    <div className="relative w-full h-screen overflow-hidden bg-[#0a0a0f]">
      {/* 开场动画 */}
      <AnimatePresence>
        {showIntro && (
          <IntroAnimation 
            onComplete={() => {
              setShowIntro(false);
              setShowUI(true);
              sessionStorage.setItem('qk_has_seen_intro', 'true');
            }} 
          />
        )}
      </AnimatePresence>
      
      {/* 3D 地球背景 */}
      <div className="absolute inset-0 z-[1]">
        <Earth3D 
          mode="default" 
          rotationSpeed={0.0005}
          enableControls={false}
          cameraPosition={[0, 0, 15]}
        />
      </div>
      
      {/* UI 层 */}
      <AnimatePresence>
        {showUI && (
          <motion.div 
            className="relative z-10 w-full h-full flex flex-col"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8, ease: [0.4, 0, 0.2, 1] }}
          >
            {/* 顶部时钟 */}
            <div className="flex-1 flex items-start justify-center pt-16">
              <Clock />
            </div>
            
            {/* 底部导航按钮 */}
            <motion.div 
              className="flex items-end justify-center pb-20 gap-6"
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
            >
              <GlassButton 
                onClick={() => handleNavigate('/search')}
                variant="accent"
                icon="🔍"
              >
                搜索
              </GlassButton>
              
              <GlassButton 
                onClick={() => handleNavigate('/about')}
                icon="ℹ️"
              >
                网站详情
              </GlassButton>
              
              <GlassButton 
                onClick={() => handleNavigate('/visual')}
                icon="🌍"
              >
                新闻可视化
              </GlassButton>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* 标题 (仅在UI显示后显示) */}
      <AnimatePresence>
        {showUI && (
          <motion.div
            className="absolute top-8 left-8 z-20"
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5, duration: 0.5 }}
          >
            <h1 className="font-['Orbitron'] text-2xl text-white/80">
              <span className="text-[#00d4ff]">Quick</span>News
            </h1>
            <p className="text-white/40 text-xs mt-1">3D 新闻可视化系统</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/**
 * 开场动画组件
 * 模拟从地面拉升至太空，地球升起的效果
 */
function IntroAnimation({ onComplete }) {
  const [phase, setPhase] = useState(0);
  
  useEffect(() => {
    // 阶段 1: 地面拉升 (0-800ms)
    const phase1 = setTimeout(() => setPhase(1), 100);
    
    // 阶段 2: 地球升起 (800-2000ms)
    const phase2 = setTimeout(() => setPhase(2), 800);
    
    // 阶段 3: 视角拉远 (2000-3000ms)
    const phase3 = setTimeout(() => setPhase(3), 2000);
    
    // 阶段 4: 淡出 (3000-4000ms)
    const phase4 = setTimeout(() => setPhase(4), 3000);
    
    return () => {
      clearTimeout(phase1);
      clearTimeout(phase2);
      clearTimeout(phase3);
      clearTimeout(phase4);
    };
  }, []);
  
  return (
    <motion.div
      className="fixed inset-0 z-50 flex items-center justify-center bg-[#0a0a0f]"
      initial={{ opacity: 1 }}
      animate={{ opacity: phase === 4 ? 0 : 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 1, ease: 'easeInOut' }}
      onAnimationComplete={() => phase === 4 && onComplete && onComplete()}
    >
      {/* 城市剪影 (阶段 1) */}
      <AnimatePresence>
        {phase === 0 && (
          <motion.div
            className="absolute inset-0 flex items-end justify-center"
            initial={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -200 }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          >
            <CitySilhouette />
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* 地球升起 (阶段 2-3) */}
      {(phase === 1 || phase === 2 || phase === 3) && (
        <motion.div
          className="relative"
          initial={{ scale: 0.3, y: 300, opacity: 0 }}
          animate={{ 
            scale: phase === 3 ? 0.7 : 1, 
            y: phase === 3 ? -50 : 0,
            opacity: 1 
          }}
          transition={{ 
            duration: phase === 3 ? 1 : 1.2, 
            ease: phase === 3 ? 'easeInOut' : [0.34, 1.56, 0.64, 1]
          }}
        >
          {/* 地球光晕 */}
          <div className="absolute inset-0 rounded-full bg-[#00d4ff]/20 blur-3xl scale-150" />
          
          {/* 简化地球 (CSS 实现) */}
          <div className="relative w-48 h-48 md:w-64 md:h-64 rounded-full overflow-hidden shadow-2xl">
            <div 
              className="absolute inset-0 rounded-full"
              style={{
                background: 'radial-gradient(circle at 30% 30%, #4a90d9 0%, #1a4d7a 50%, #0a1f3d 100%)',
              }}
            />
            {/* 大陆轮廓 */}
            <div 
              className="absolute inset-0 rounded-full opacity-60"
              style={{
                background: `
                  radial-gradient(ellipse 30% 20% at 25% 35%, #2d5a3d 0%, transparent 70%),
                  radial-gradient(ellipse 25% 30% at 70% 40%, #2d5a3d 0%, transparent 70%),
                  radial-gradient(ellipse 20% 25% at 45% 70%, #2d5a3d 0%, transparent 70%),
                  radial-gradient(ellipse 15% 20% at 80% 65%, #2d5a3d 0%, transparent 70%)
                `,
              }}
            />
            {/* 大气层 */}
            <div 
              className="absolute inset-[-10%] rounded-full"
              style={{
                background: 'radial-gradient(circle at 30% 30%, transparent 60%, rgba(0, 212, 255, 0.3) 80%, rgba(0, 212, 255, 0.1) 100%)',
              }}
            />
          </div>
          
          {/* 旋转动画 */}
          <motion.div
            className="absolute inset-0"
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
          >
            <div className="absolute top-0 left-1/2 w-1 h-4 bg-[#00d4ff]/50 -translate-x-1/2" />
          </motion.div>
        </motion.div>
      )}
      
      {/* 标题文字 (阶段 3) */}
      {phase === 3 && (
        <motion.div
          className="absolute bottom-1/4 text-center"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <h1 className="font-['Orbitron'] text-4xl md:text-6xl text-white">
            <span className="text-[#00d4ff]">Quick</span>News
          </h1>
          <p className="text-white/60 mt-2 text-lg">全球新闻可视化系统</p>
        </motion.div>
      )}
    </motion.div>
  );
}

/**
 * 城市剪影组件
 */
function CitySilhouette() {
  return (
    <svg 
      viewBox="0 0 1200 300" 
      className="w-full h-64 opacity-50"
      preserveAspectRatio="xMidYMax slice"
    >
      <defs>
        <linearGradient id="cityGradient" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#1a1a2e" />
          <stop offset="100%" stopColor="#0a0a0f" />
        </linearGradient>
      </defs>
      <path
        fill="url(#cityGradient)"
        d="M0,300 L0,200 L30,200 L30,150 L60,150 L60,180 L90,180 L90,100 L120,100 L120,200 L150,200 L150,120 L180,120 L180,180 L210,180 L210,80 L240,80 L240,200 L270,200 L270,140 L300,140 L300,200 L330,200 L330,90 L360,90 L360,180 L390,180 L390,160 L420,160 L420,200 L450,200 L450,110 L480,110 L480,190 L510,190 L510,130 L540,130 L540,200 L570,200 L570,70 L600,70 L600,200 L630,200 L630,140 L660,140 L660,180 L690,180 L690,100 L720,100 L720,200 L750,200 L750,150 L780,150 L780,200 L810,200 L810,120 L840,120 L840,180 L870,180 L870,160 L900,160 L900,200 L930,200 L930,90 L960,90 L960,190 L990,190 L990,130 L1020,130 L1020,200 L1050,200 L1050,110 L1080,110 L1080,180 L1110,180 L1110,140 L1140,140 L1140,200 L1170,200 L1170,160 L1200,160 L1200,300 Z"
      />
    </svg>
  );
}
