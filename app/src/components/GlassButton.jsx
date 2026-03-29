/**
 * 玻璃态按钮组件
 * Glassmorphism 风格的按钮
 */

import React from 'react';
import { motion } from 'framer-motion';

export default function GlassButton({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  className = '',
  disabled = false,
  icon = null,
}) {
  // 尺寸配置
  const sizeClasses = {
    small: 'px-4 py-2 text-sm',
    medium: 'px-8 py-4 text-base',
    large: 'px-12 py-5 text-lg',
  };
  
  // 变体配置
  const variantClasses = {
    primary: 'bg-white/5 border-white/10 hover:bg-white/10 hover:border-[#00d4ff]/50',
    secondary: 'bg-white/3 border-white/5 hover:bg-white/8 hover:border-white/20',
    accent: 'bg-[#00d4ff]/10 border-[#00d4ff]/30 hover:bg-[#00d4ff]/20 hover:border-[#00d4ff]/60',
  };
  
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      className={`
        relative overflow-hidden
        glass rounded-xl font-['Orbitron'] text-white
        transition-all duration-300 ease-out
        disabled:opacity-50 disabled:cursor-not-allowed
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
      whileHover={{ 
        scale: disabled ? 1 : 1.05,
        boxShadow: disabled ? 'none' : '0 0 30px rgba(0, 212, 255, 0.4)'
      }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
    >
      {/* 背景光效 */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
        initial={{ x: '-100%' }}
        whileHover={{ x: '100%' }}
        transition={{ duration: 0.6, ease: 'easeInOut' }}
      />
      
      {/* 内容 */}
      <span className="relative z-10 flex items-center justify-center gap-2">
        {icon && <span className="text-lg">{icon}</span>}
        {children}
      </span>
      
      {/* 边框发光 */}
      <div className="absolute inset-0 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-300">
        <div className="absolute inset-0 rounded-xl glow-border" />
      </div>
    </motion.button>
  );
}
