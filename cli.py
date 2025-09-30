import typer
import os
from typing import Optional

app = typer.Typer(help="CLI for app scaffolding.")


# ---------------------------
# Helpers
# ---------------------------
def get_base_path(app_name: str) -> str:
    # Get the absolute path of the CLI script
    cli_dir = os.path.dirname(os.path.abspath(__file__))

    # Go up until project root (assuming CLI is inside api/src/core/cli.py for example)
    project_root = os.path.abspath(cli_dir)

    # Build apps/<app_name> path
    return os.path.join(project_root, "src", "apps", app_name)


def write_file(path: str, content: str):
    """Create a file if it does not exist."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"✅ Created: {path}")


def ensure_package(path: str):
    """Ensure a folder exists and has an __init__.py."""
    os.makedirs(path, exist_ok=True)
    init_file = os.path.join(path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            f.write('"""Package initializer."""\n\n')


# ---------------------------
# Commands
# ---------------------------
@app.command()
def app_create(app_name: str):
    """Create a new app directory structure."""
    if not app_name.isidentifier():
        print("❌ Invalid app name. Use only letters, numbers, and underscores.")
        raise typer.Exit(1)

    base_path = get_base_path(app_name)
    ensure_package(base_path)

    for folder in ["models", "repositories", "services", "routers", "schemas"]:
        ensure_package(os.path.join(base_path, folder))

    # Create __init__.py for the app
    app_init_content = f'"""{app_name.title()} app."""\n\n'
    write_file(os.path.join(base_path, "__init__.py"), app_init_content)

    print(f"✅ App directory created at {base_path}")


@app.command()
def model(
    app_name: str, 
    model_name: str, 
    fields: Optional[str] = typer.Option(None, "--fields", "-f", help="Fields in format 'name:type,name:type'")
):
    """Create model + repository + service + router + schemas for this model."""
    if not model_name.isidentifier():
        print("❌ Invalid model name. Use only letters, numbers, and underscores.")
        raise typer.Exit(1)

    base_path = get_base_path(app_name)
    model_name_lower = model_name.lower()
    model_name_upper = model_name.upper()

    # Parse fields if provided
    field_list = []
    if fields:
        for field in fields.split(","):
            field = field.strip()
            if ":" in field:
                name, ftype = field.split(":", 1)
                field_list.append((name.strip(), ftype.strip()))

    # ---------------------------
    # Model
    # ---------------------------
    model_file = os.path.join(base_path, "models", f"{model_name_lower}.py")
    model_content = f'''"""{model_name} model."""

from sqlmodel import Field
from src.core.database import BaseModel


class {model_name}(BaseModel, table=True):
    """{model_name} model class."""
    
    __tablename__ = "{app_name}_{model_name_lower}s"  # type: ignore
'''
    
    # Add fields
    if field_list:
        for field_name, field_type in field_list:
            model_content += f"    {field_name}: {field_type} = Field()\n"
    else:
        model_content += "    # Add your fields here\n"
        model_content += "    name: str = Field()\n"
    
    model_content += "\n"
    write_file(model_file, model_content)

    # ---------------------------
    # Schemas
    # ---------------------------
    schemas_file = os.path.join(base_path, "schemas", f"{model_name_lower}.py")
    schemas_content = f'''"""{model_name} schemas."""

from typing import Optional
from pydantic import BaseModel


class {model_name}Create(BaseModel):
    """Schema for creating a {model_name_lower}."""
'''
    
    if field_list:
        for field_name, field_type in field_list:
            schemas_content += f"    {field_name}: {field_type}\n"
    else:
        schemas_content += "    name: str\n"
    
    schemas_content += f'''

class {model_name}Update(BaseModel):
    """Schema for updating a {model_name_lower}."""
'''
    
    if field_list:
        for field_name, field_type in field_list:
            # Make all fields optional for update
            schemas_content += f"    {field_name}: Optional[{field_type}] = None\n"
    else:
        schemas_content += "    name: Optional[str] = None\n"
    
    schemas_content += "\n"
    write_file(schemas_file, schemas_content)

    # ---------------------------
    # Repository
    # ---------------------------
    repo_file = os.path.join(base_path, "repositories", f"{model_name_lower}_repository.py")
    repo_content = f'''"""{model_name} repository."""

from src.core.bases.base_repository import BaseRepository
from src.apps.{app_name}.models.{model_name_lower} import {model_name}


class {model_name}Repository(BaseRepository[{model_name}]):
    """{model_name} repository class."""
    
    model = {model_name}
'''
    write_file(repo_file, repo_content)

    # ---------------------------
    # Service
    # ---------------------------
    service_file = os.path.join(base_path, "services", f"{model_name_lower}_service.py")
    service_content = f'''"""{model_name} service."""

from typing import Any, Dict
from src.core.bases.base_service import BaseService
from src.apps.{app_name}.repositories.{model_name_lower}_repository import {model_name}Repository
from src.apps.{app_name}.models.{model_name_lower} import {model_name}


class {model_name}Service(BaseService[{model_name}]):
    """{model_name} service class."""
    
    def __init__(self, repository: {model_name}Repository):
        super().__init__(repository)

    async def _validate_create(self, create_data: Dict[str, Any]) -> None:
        """Validate data before creation."""
        # Add your business logic validation here
        pass

    async def _validate_update(
        self, 
        item_id: Any, 
        update_data: Dict[str, Any], 
        existing_item: {model_name}
    ) -> None:
        """Validate data before update."""
        # Add your business logic validation here
        pass

    async def _validate_delete(self, item_id: Any, existing_item: {model_name}) -> None:
        """Validate before soft delete."""
        # Add your business logic validation here
        pass

    async def _validate_force_delete(self, item_id: Any, existing_item: {model_name}) -> None:
        """Validate before force delete."""
        # Add your business logic validation here
        pass
'''
    write_file(service_file, service_content)

    # ---------------------------
    # Router
    # ---------------------------
    router_file = os.path.join(base_path, "routers", f"{model_name_lower}_router.py")
    router_content = f'''"""{model_name} router."""

from src.core.database import get_session
from src.core.bases.base_router import BaseRouter
from src.apps.{app_name}.services.{model_name_lower}_service import {model_name}Service
from src.apps.{app_name}.repositories.{model_name_lower}_repository import {model_name}Repository
from src.apps.{app_name}.schemas.{model_name_lower} import {model_name}Create, {model_name}Update


def get_{model_name_lower}_repository():
    """Get {model_name_lower} repository instance."""
    return {model_name}Repository(get_session) #type:ignore


def get_{model_name_lower}_service():
    """Get {model_name_lower} service instance."""
    repository = get_{model_name_lower}_repository()
    return {model_name}Service(repository)


class {model_name}Router(BaseRouter):
    """{model_name} router class."""
    
    def __init__(self):
        super().__init__(
            service=get_{model_name_lower}_service(),
            create_schema={model_name}Create,
            update_schema={model_name}Update,
            prefix="/{model_name_lower}s",
            tags=["{model_name.title()}s"]
        )


# Router instance
router = {model_name}Router().get_router()
'''
    write_file(router_file, router_content)

    # ---------------------------
    # Update app __init__.py to export the router
    # ---------------------------
    app_init_file = os.path.join(base_path, "__init__.py")
    export_line = f"from .routers.{model_name_lower}_router import router as {model_name_lower}_router\n"
    
    # Read existing content and append if not already there
    if os.path.exists(app_init_file):
        with open(app_init_file, "r") as f:
            content = f.read()
        
        if export_line not in content:
            with open(app_init_file, "a") as f:
                f.write(export_line)
    else:
        with open(app_init_file, "w") as f:
            f.write(export_line)

    print(f"🎉 Model '{model_name}' added to app '{app_name}' successfully.")
    print(f"📁 Files created:")
    print(f"   - models/{model_name_lower}.py")
    print(f"   - schemas/{model_name_lower}.py") 
    print(f"   - repositories/{model_name_lower}_repository.py")
    print(f"   - services/{model_name_lower}_service.py")
    print(f"   - routers/{model_name_lower}_router.py")


@app.command()
def full(
    app_name: str, 
    model_name: str, 
    fields: Optional[str] = typer.Option(None, "--fields", "-f", help="Fields in format 'name:type,name:type'")
):
    """Create full app with one model + repo + service + router."""
    app_create(app_name)
    model(app_name, model_name, fields)


@app.command()
def list_apps():
    """List all existing apps."""
    base_path = os.path.join(get_base_path(""), "..")  # Go up from apps directory
    apps_path = os.path.join(base_path, "apps")
    
    if not os.path.exists(apps_path):
        print("❌ No apps directory found.")
        return
    
    apps = [d for d in os.listdir(apps_path) 
           if os.path.isdir(os.path.join(apps_path, d)) and not d.startswith('_')]
    
    if not apps:
        print("📁 No apps found.")
        return
    
    print("📁 Existing apps:")
    for app in apps:
        app_path = os.path.join(apps_path, app)
        models_path = os.path.join(app_path, "models")
        models = []
        
        if os.path.exists(models_path):
            models = [f.replace('.py', '') for f in os.listdir(models_path) 
                     if f.endswith('.py') and not f.startswith('_')]
        
        print(f"  🏷️  {app}:")
        for model in models:
            print(f"     📄 {model}")


# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    app()

    """
    # Create a new blog app with Post model and fields
python cli.py full blog Post --fields "title:str,content:str,author:str"

# Or using the short form
python cli.py full blog Post -f "title:str,content:str,author:str"

# Add another model to existing app
python cli.py model blog Comment -f "content:str,post_id:int,author:str"

# Create model without specific fields (uses default)
python cli.py model blog Category
    """