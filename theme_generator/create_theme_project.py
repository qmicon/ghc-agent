# Usage: python create_theme_project.py
# This script creates a new theme project directory with a random name inside 'theme-projects'.
# The structure is:
# theme-projects/<random_project_name>/
#   ├── theme_code/         # Contains a copy of the dawn-main theme
#   └── intermediate_files/ # For screenshots, markdown, etc.
# The script prints the project directory name.

import os
import shutil
import uuid

THEME_PROJECTS_DIR = "theme-projects"
DAWN_MAIN_DIR = "dawn-main"  # Assumes dawn-main is in the current working directory
INTERMEDIATE_DIR_NAME = "intermediate_files"
THEME_CODE_DIR_NAME = "theme_code"


def create_theme_project():
    # Generate a random project name
    project_name = f"theme_{uuid.uuid4().hex[:8]}"
    project_path = os.path.join(THEME_PROJECTS_DIR, project_name)
    theme_code_path = os.path.join(project_path, THEME_CODE_DIR_NAME)
    intermediate_path = os.path.join(project_path, INTERMEDIATE_DIR_NAME)

    # Create directories
    os.makedirs(theme_code_path, exist_ok=False)
    os.makedirs(intermediate_path, exist_ok=False)

    # Copy dawn-main theme into theme_code directory
    if not os.path.exists(DAWN_MAIN_DIR):
        raise FileNotFoundError(f"{DAWN_MAIN_DIR} not found in current directory.")
    shutil.copytree(DAWN_MAIN_DIR, theme_code_path, dirs_exist_ok=True)

    print(project_name)
    return project_name

if __name__ == "__main__":
    create_theme_project() 