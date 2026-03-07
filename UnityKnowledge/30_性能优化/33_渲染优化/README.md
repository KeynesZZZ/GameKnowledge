# 渲染优化

> Unity 渲染性能优化

## 主题

- DrawCall 优化
- 批处理(Batching)
- LOD 系统
- 遮挡剔除(Occlusion Culling)
- GPU Instancing
- Overdraw 优化

## 核心文档

### 实战案例
- [UI卡顿优化全流程](./【实战案例】UI卡顿优化全流程.md) - 完整优化流程：30fps→60fps

### 最佳实践
- [Overdraw优化实战](./【最佳实践】Overdraw优化实战.md) - GPU过度绘制检测与优化
- [LOD系统实战指南](./【最佳实践】LOD系统实战指南.md) - LOD配置、过渡优化、Billboard
- [遮挡剔除实战](./【最佳实践】遮挡剔除实战.md) - Occlusion Culling配置与Occlusion Portal
- [UI性能优化](./【最佳实践】UI性能优化.md)
- [3D渲染优化指南](./【最佳实践】3D渲染优化指南.md)
- [光照与烘焙优化](./【最佳实践】光照与烘焙优化.md)
- [粒子系统优化](./【最佳实践】粒子系统优化.md)

### 教程
- [Frame Debugger渲染诊断流程](./【教程】Frame Debugger渲染诊断流程.md) - 系统化渲染问题诊断
- [渲染性能优化](../../30_性能优化/【教程】渲染性能优化.md)

### 性能数据
- [UGUI DrawCall影响因素](./【性能数据】UGUI DrawCall影响因素.md)
- [Shader性能优化](./【性能数据】Shader性能优化.md)
- [纹理压缩格式对比](./【性能数据】纹理压缩格式对比.md)

## 优化检查清单

### DrawCall优化
- [ ] 合理拆分Canvas
- [ ] 使用图集
- [ ] 避免UI重叠
- [ ] 优化粒子系统
- [ ] 使用对象池复用UI

### GPU优化
- [ ] 优化Overdraw
- [ ] 配置LOD系统
- [ ] 启用遮挡剔除
- [ ] 使用GPU Instancing

## 相关链接

- [性能分析工具](../【教程】性能分析工具.md)
- [UI卡顿优化实战](./【实战案例】UI卡顿优化全流程.md)
