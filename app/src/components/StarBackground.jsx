/**
 * 星空背景组件
 * 使用 Canvas 绘制动态星空粒子效果
 */

import React, { useEffect, useRef } from 'react';

export default function StarBackground() {
  const canvasRef = useRef(null);
  const animationRef = useRef(null);
  const starsRef = useRef([]);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 设置画布尺寸
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      initStars();
    };
    
    // 初始化星星
    const initStars = () => {
      const starCount = Math.floor((canvas.width * canvas.height) / 3000);
      starsRef.current = [];
      
      for (let i = 0; i < starCount; i++) {
        starsRef.current.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          size: Math.random() * 1.5 + 0.5,
          speedX: (Math.random() - 0.5) * 0.2,
          speedY: (Math.random() - 0.5) * 0.2,
          opacity: Math.random() * 0.8 + 0.2,
          twinkleSpeed: Math.random() * 0.02 + 0.01,
          twinklePhase: Math.random() * Math.PI * 2,
        });
      }
    };
    
    // 动画循环
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // 绘制渐变背景
      const gradient = ctx.createRadialGradient(
        canvas.width / 2, canvas.height / 2, 0,
        canvas.width / 2, canvas.height / 2, canvas.width
      );
      gradient.addColorStop(0, '#0a0a15');
      gradient.addColorStop(0.5, '#0a0a0f');
      gradient.addColorStop(1, '#050508');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // 绘制星星
      starsRef.current.forEach(star => {
        // 更新位置
        star.x += star.speedX;
        star.y += star.speedY;
        
        // 边界处理
        if (star.x < 0) star.x = canvas.width;
        if (star.x > canvas.width) star.x = 0;
        if (star.y < 0) star.y = canvas.height;
        if (star.y > canvas.height) star.y = 0;
        
        // 闪烁效果
        star.twinklePhase += star.twinkleSpeed;
        const twinkle = Math.sin(star.twinklePhase) * 0.3 + 0.7;
        const currentOpacity = star.opacity * twinkle;
        
        // 绘制星星
        ctx.beginPath();
        ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${currentOpacity})`;
        ctx.fill();
        
        // 大星星添加光晕
        if (star.size > 1.2) {
          ctx.beginPath();
          ctx.arc(star.x, star.y, star.size * 2, 0, Math.PI * 2);
          const glowGradient = ctx.createRadialGradient(
            star.x, star.y, 0,
            star.x, star.y, star.size * 2
          );
          glowGradient.addColorStop(0, `rgba(255, 255, 255, ${currentOpacity * 0.3})`);
          glowGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
          ctx.fillStyle = glowGradient;
          ctx.fill();
        }
      });
      
      // 偶尔绘制流星
      if (Math.random() < 0.005) {
        drawMeteor();
      }
      
      animationRef.current = requestAnimationFrame(animate);
    };
    
    // 绘制流星
    const drawMeteor = () => {
      const startX = Math.random() * canvas.width;
      const startY = Math.random() * canvas.height * 0.5;
      const length = 50 + Math.random() * 100;
      const angle = Math.PI / 4 + (Math.random() - 0.5) * 0.3;
      
      const endX = startX - Math.cos(angle) * length;
      const endY = startY + Math.sin(angle) * length;
      
      const meteorGradient = ctx.createLinearGradient(startX, startY, endX, endY);
      meteorGradient.addColorStop(0, 'rgba(255, 255, 255, 0.8)');
      meteorGradient.addColorStop(0.5, 'rgba(255, 255, 255, 0.3)');
      meteorGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');
      
      ctx.beginPath();
      ctx.moveTo(startX, startY);
      ctx.lineTo(endX, endY);
      ctx.strokeStyle = meteorGradient;
      ctx.lineWidth = 2;
      ctx.stroke();
    };
    
    // 初始化
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    animate();
    
    // 清理
    return () => {
      window.removeEventListener('resize', resizeCanvas);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);
  
  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0 }}
    />
  );
}
