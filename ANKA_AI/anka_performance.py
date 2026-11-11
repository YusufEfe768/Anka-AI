# ── ANKA PERFORMANS OPTİMİZASYON MODÜLü ─────────────────────────────────────
# RAM ve CPU kullanımını minimize eder
import os, sys, gc, threading, time, psutil

class PerformanceManager:
    """Anka'nın kaynak kullanımını optimize eder"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'): return
        self._initialized = True
        self._lazy_modules = {}  # Henüz yüklenmemiş modüller
        self._loaded_modules = {}  # Yüklü modüller
        self.running = True
        self._start_optimizer()
    
    def _start_optimizer(self):
        """Arka planda hafıza optimizasyonu yap"""
        def _loop():
            while self.running:
                try:
                    ram = psutil.virtual_memory().percent
                    # RAM %85 üzerindeyse agresif temizlik yap
                    if ram > 85:
                        gc.collect()
                        print(f"[ANKA] RAM yüksek (%{ram:.0f}), temizlik yapıldı.")
                    # RAM %90 üzerindeyse modülleri boşalt
                    if ram > 90:
                        self._unload_unused()
                except: pass
                time.sleep(30)  # 30 saniyede bir kontrol
        threading.Thread(target=_loop, daemon=True).start()
    
    def lazy_import(self, module_name):
        """Modülü sadece gerektiğinde yükle"""
        if module_name not in self._loaded_modules:
            try:
                import importlib
                mod = importlib.import_module(module_name)
                self._loaded_modules[module_name] = mod
                return mod
            except ImportError:
                return None
        return self._loaded_modules[module_name]
    
    def _unload_unused(self):
        """Uzun süredir kullanılmayan modülleri temizle"""
        # Yalnızca güvenli modülleri temizle
        safe_to_unload = ['feedparser', 'qrcode', 'PyPDF2']
        for mod in safe_to_unload:
            if mod in sys.modules:
                del sys.modules[mod]
        gc.collect()
    
    def get_stats(self):
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        return {
            "cpu": cpu,
            "ram_percent": ram.percent,
            "ram_used_mb": ram.used // 1024 // 1024,
            "ram_free_mb": ram.available // 1024 // 1024
        }
    
    def optimize_now(self):
        """Anında optimizasyon"""
        before = psutil.virtual_memory().percent
        gc.collect()
        self._unload_unused()
        after = psutil.virtual_memory().percent
        freed = before - after
        return f"✅ Optimizasyon tamamlandı! RAM: %{before:.0f} → %{after:.0f} ({freed:.1f}% serbest)"
    
    def stop(self):
        self.running = False


# ── Hafif Thread Yöneticisi ───────────────────────────────────────────────────
class LightThreadManager:
    """Thread sayısını minimize eder"""
    _pool = []
    _max_threads = 5  # Maksimum 5 thread
    
    @classmethod
    def run(cls, func, *args, **kwargs):
        # Biten thread'leri temizle
        cls._pool = [t for t in cls._pool if t.is_alive()]
        # Max thread sayısını aşmıyorsa çalıştır
        if len(cls._pool) < cls._max_threads:
            t = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
            cls._pool.append(t)
            t.start()
            return t
        else:
            # Direkt çalıştır (thread açmadan)
            func(*args, **kwargs)
            return None
    
    @classmethod
    def count(cls):
        cls._pool = [t for t in cls._pool if t.is_alive()]
        return len(cls._pool)


# Singleton instance
perf = PerformanceManager()
