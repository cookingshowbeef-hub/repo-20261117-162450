"""Make pip-installed NVIDIA CUDA 12 DLLs (cuBLAS, cuDNN, NVRTC, runtime) loadable on Windows. Import before ctranslate2 / cupy."""
import glob, os, site
_dirs = []
for sp in site.getsitepackages() + [site.getusersitepackages()]:
    _dirs += glob.glob(os.path.join(sp, "nvidia", "*", "bin"))
for d in _dirs:
    os.add_dll_directory(d)
os.environ["PATH"] = os.pathsep.join(_dirs + [os.environ.get("PATH", "")])
