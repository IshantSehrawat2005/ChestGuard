/**
 * ChestGuard NeuralScan — X-Ray Viewer
 * Interactive X-ray viewer with zoom, pan, brightness/contrast controls.
 */

class XRayViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.isDragging = false;
        this.lastX = 0;
        this.lastY = 0;
        
        this.initZoomPan();
    }
    
    initZoomPan() {
        // Mouse wheel zoom
        this.container.addEventListener('wheel', (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            this.scale = Math.max(0.5, Math.min(3, this.scale * delta));
            this.applyTransform();
        });
        
        // Pan on drag
        this.container.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;
            this.isDragging = true;
            this.lastX = e.clientX;
            this.lastY = e.clientY;
            this.container.style.cursor = 'grabbing';
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!this.isDragging) return;
            const dx = e.clientX - this.lastX;
            const dy = e.clientY - this.lastY;
            this.offsetX += dx;
            this.offsetY += dy;
            this.lastX = e.clientX;
            this.lastY = e.clientY;
            this.applyTransform();
        });
        
        document.addEventListener('mouseup', () => {
            this.isDragging = false;
            this.container.style.cursor = 'grab';
        });
        
        // Double click to reset
        this.container.addEventListener('dblclick', () => {
            this.scale = 1;
            this.offsetX = 0;
            this.offsetY = 0;
            this.applyTransform();
        });
        
        this.container.style.cursor = 'grab';
    }
    
    applyTransform() {
        const imgs = this.container.querySelectorAll('img');
        imgs.forEach(img => {
            img.style.transform = `translate(${this.offsetX}px, ${this.offsetY}px) scale(${this.scale})`;
            img.style.transformOrigin = 'center center';
        });
    }
    
    reset() {
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.applyTransform();
    }
}

// Initialize viewer when results are displayed
document.addEventListener('DOMContentLoaded', () => {
    // Will be initialized after images are loaded
    window.xrayViewer = null;
    
    // Observer to init viewer when heatmap tab becomes visible
    const observer = new MutationObserver(() => {
        const heatmapPane = document.getElementById('tab-heatmaps');
        if (heatmapPane && heatmapPane.classList.contains('active') && !window.xrayViewer) {
            window.xrayViewer = new XRayViewer('xray-viewer');
        }
    });
    
    const tabContent = document.querySelector('.tab-content');
    if (tabContent) {
        observer.observe(tabContent, { subtree: true, attributes: true, attributeFilter: ['class'] });
    }
});
