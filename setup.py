from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import sys
import shutil

class PostInstallCommand(install):
    """在安装后从 ModelScope 拉取数据集到 lib/ref/voices。"""
    def run(self):
        install.run(self)
        try:
            from modelscope.hub.snapshot_download import snapshot_download
        except Exception as e:
            print(f"[setup] 未找到 modelscope，跳过数据集拉取：{e}")
            return

        dataset_id = os.environ.get('MS_DATASET_ID', '').strip()
        if not dataset_id:
            print("[setup] 未设置 MS_DATASET_ID，跳过从 ModelScope 拉取。")
            return

        project_root = os.path.dirname(os.path.abspath(__file__))
        voices_dir = os.path.join(project_root, 'lib', 'ref', 'voices')
        os.makedirs(voices_dir, exist_ok=True)

        try:
            print(f"[setup] 从 ModelScope 拉取数据集：{dataset_id}")
            local_dir = snapshot_download(dataset_id, repo_type='dataset')
            copied = 0
            for root, _, files in os.walk(local_dir):
                for fname in files:
                    if fname.lower().endswith('.wav'):
                        src = os.path.join(root, fname)
                        dst = os.path.join(voices_dir, fname)
                        if not os.path.exists(dst):
                            shutil.copy2(src, dst)
                            copied += 1
            print(f"[setup] 已复制 {copied} 个 .wav 到 {voices_dir}")
        except Exception as e:
            print(f"[setup] 拉取/复制数据集失败：{e}")

setup(
    name='arknights-auto-dubbing',
    version='0.1.0',
    description='Auto OCR + TTS for Arknights',
    packages=find_packages(exclude=['venv', 'TEMP']),
    include_package_data=True,
    install_requires=[],  # 使用 requirements.txt 管理
    cmdclass={
        'install': PostInstallCommand,
    },
) 