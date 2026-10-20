import os
import platform
import subprocess

VCPKG_PATH = os.path.join(os.path.dirname(__file__), "dependencies", "vcpkg")

PACKAGES = ["eigen3"]


def install():
    # ponytail: no version check here; CMakeLists.txt's cmake_minimum_required enforces it.
    try:
        subprocess.check_output(["cmake", "--version"])
    except OSError as err:
        raise RuntimeError("CMake must be installed") from err

    install_vcpkg_dependencies()
    build()


def install_vcpkg_dependencies():
    print(f"system is {platform.system()}")
    if platform.system() == "Windows":
        subprocess.run("bootstrap-vcpkg.bat", cwd=VCPKG_PATH, shell=True)
    else:
        subprocess.run(os.path.join(VCPKG_PATH, "bootstrap-vcpkg.sh"))
    for package in PACKAGES:
        print(f"installing {package}")
        if platform.system() == "Windows":
            triplet = ":x64-windows"
        elif platform.system() == "Linux":
            triplet = ":x64-linux"
        else:
            triplet = ":x64-osx"
        subprocess.check_call([os.path.join(VCPKG_PATH, "vcpkg"), "install", package + triplet])


def build():
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "build"))
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)

    subprocess.check_call(["cmake", "../"], cwd=build_dir)
    subprocess.check_call(["cmake", "--build", ".", "--config", "Release"], cwd=build_dir)

    print([i for i in os.listdir(os.path.join(os.path.dirname(__file__), "binaries"))])


if __name__ == "__main__":
    install()
