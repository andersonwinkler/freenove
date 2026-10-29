#!/usr/bin/env python3
import os
import pwd
import shutil
import tempfile

# Product-scoped root so other Freenove kits can live beside this one
# under /opt/freenove/<product>/.
INSTALL_ROOT = '/opt/freenove/tower-cooler'
APP_DIR = os.path.join(INSTALL_ROOT, 'app')
LIB_DIR = os.path.join(INSTALL_ROOT, 'lib')

def get_raspberry_pi_model():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.readlines()
        for line in cpuinfo:
            if line.startswith('Model'):
                model_info = line.strip().split(':')[-1].strip().split('Model')[0].strip()
                return model_info
        return 'Unknown Raspberry Pi Model'
    except Exception as e:
        print(f'Error reading /proc/cpuinfo: {e}')
        return 'Error Reading'

def run_command(command):
    """Execute the specified shell command"""
    print(f'Running: {command}')
    result = os.system(command)
    if result != 0:
        raise Exception(f'Command failed: {command}')

def get_install_user():
    """Resolve the real user when setup is run with or without sudo."""
    sudo_user = os.environ.get('SUDO_USER')
    if sudo_user:
        return sudo_user
    try:
        return os.getlogin()
    except Exception:
        return os.environ.get('USER') or 'pi'

def ensure_install_root(username):
    run_command(f'sudo mkdir -p {LIB_DIR} {APP_DIR}')
    run_command(f'sudo chown -R {username}:{username} {INSTALL_ROOT}')

def _cmake_cache_value(cache_path, key):
    """Return the value for KEY from a CMakeCache.txt, or None."""
    prefix = f'{key}:'
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith(prefix):
                    # Format: KEY:TYPE=value
                    _, _, value = line.rstrip('\n').partition('=')
                    return value
    except OSError:
        return None
    return None

def prepare_cmake_build_dir(native_dir, build_dir):
    """Drop a stale CMake build tree if the source/build paths moved (e.g. repo rename)."""
    cache_path = os.path.join(build_dir, 'CMakeCache.txt')
    if not os.path.isfile(cache_path):
        return

    expected_source = os.path.realpath(native_dir)
    expected_build = os.path.realpath(build_dir)
    cached_source = _cmake_cache_value(cache_path, 'CMAKE_HOME_DIRECTORY')
    cached_build = _cmake_cache_value(cache_path, 'CMAKE_CACHEFILE_DIR')

    stale = False
    if cached_source and os.path.realpath(cached_source) != expected_source:
        stale = True
    if cached_build and os.path.realpath(cached_build) != expected_build:
        stale = True

    if stale:
        print(
            f'Stale CMake cache detected under {build_dir} '
            f'(was source={cached_source!r}, build={cached_build!r}); removing it.')
        shutil.rmtree(build_dir)

def install_ws2812_lib(script_dir):
    """Build vendored Freenove WS2812 lib and install under /opt/freenove/tower-cooler/lib."""
    native_dir = os.path.join(script_dir, 'native', 'ws2812')
    build_dir = os.path.join(native_dir, 'build')
    if not os.path.isfile(os.path.join(native_dir, 'CMakeLists.txt')):
        raise Exception(f'Missing native WS2812 sources at {native_dir}')

    prepare_cmake_build_dir(native_dir, build_dir)
    run_command(
        'sudo apt install -y build-essential cmake '
        'device-tree-compiler libfdt-dev libgnutls28-dev libpio-dev')
    run_command(
        f'cmake -S {native_dir} -B {build_dir} '
        f'-DCMAKE_BUILD_TYPE=Release '
        f'-DCMAKE_INSTALL_PREFIX={INSTALL_ROOT}')
    run_command(f'cmake --build {build_dir}')
    run_command(f'sudo cmake --install {build_dir}')

def _ignore_bytecode(directory, names):
    ignored = set()
    for name in names:
        if name == '__pycache__' or name.endswith('.pyc'):
            ignored.add(name)
    return ignored

def install_app(script_dir, username):
    """Copy the Python app into /opt/freenove/tower-cooler/app."""
    code_dir = os.path.join(script_dir, 'Code')
    if not os.path.isdir(code_dir):
        raise Exception(f'Missing app sources at {code_dir}')

    staging_dir = tempfile.mkdtemp(prefix='freenove-tower-cooler-')
    try:
        staged_app = os.path.join(staging_dir, 'app')
        shutil.copytree(code_dir, staged_app, ignore=_ignore_bytecode)
        run_command(f'sudo rm -rf {APP_DIR}')
        run_command(f'sudo mkdir -p {INSTALL_ROOT}')
        run_command(f'sudo cp -a {staged_app} {APP_DIR}')
    finally:
        shutil.rmtree(staging_dir, ignore_errors=True)

    run_command(f'sudo chown -R {username}:{username} {INSTALL_ROOT}')
    run_command(f'chmod 755 {os.path.join(APP_DIR, "run_app.sh")}')

def install_uninstall_script(script_dir, username):
    """Install uninstall.sh next to app/ and lib/ under the product root."""
    src = os.path.join(script_dir, 'uninstall.sh')
    if not os.path.isfile(src):
        raise Exception(f'Missing uninstall script at {src}')
    dest = os.path.join(INSTALL_ROOT, 'uninstall.sh')
    run_command(f'sudo cp -a {src} {dest}')
    run_command(f'sudo chown {username}:{username} {dest}')
    run_command(f'chmod 755 {dest}')

def create_shortcuts():
    run_command(f'cd {APP_DIR} && python3 create_desktop_shortcut.py')

def main():
    print('Starting setup...')
    script_dir = os.path.dirname(os.path.abspath(__file__))
    username = get_install_user()
    try:
        pwd.getpwnam(username)
    except KeyError:
        username = 'pi'
        print(f'Warning: Unable to resolve install user, falling back to {username}')

    try:
        run_command('sudo apt update')
        ensure_install_root(username)

        if 'Pi 5' in get_raspberry_pi_model():
            install_ws2812_lib(script_dir)
        else:
            print('Skipping WS2812 native library: LED driver requires Raspberry Pi 5')

        run_command('sudo apt install -y python3-pip python3-luma.oled')
        install_app(script_dir, username)
        install_uninstall_script(script_dir, username)
        create_shortcuts()
        print(f'Setup complete. App installed at {APP_DIR}')
        print(f'WS2812 library directory: {LIB_DIR}')
        print(f'Uninstall with: {os.path.join(INSTALL_ROOT, "uninstall.sh")}')
    except Exception as e:
        print(f'Error occurred: {e}')


if __name__ == '__main__':
    main()
