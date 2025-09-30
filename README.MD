# FastAPI SQLModel CRUD Generator 🚀

A powerful, production-ready FastAPI boilerplate with automatic CRUD API generation using SQLModel and async PostgreSQL.

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![SQLModel](https://img.shields.io/badge/SQLModel-00a8ff?style=for-the-badge&logo=python&logoColor=white)

## ✨ Features

- ⚡ **Automatic CRUD API Generation** - Generate complete REST APIs with a single command
- 🗄️ **Async PostgreSQL Support** - Built with SQLModel and asyncpg for high performance
- 🗑️ **Soft Delete** - Built-in soft delete with restore functionality
- 🛡️ **Type Safety** - Full Python type hints and Pydantic validation
- 🏗️ **Clean Architecture** - Proper separation of concerns with repository pattern
- 🔧 **CLI Tool** - Scaffold new apps and models quickly
- 📚 **Auto Documentation** - Automatic OpenAPI/Swagger documentation
- 🚀 **Production Ready** - Error handling, logging, and health checks

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+

### Installation

1. **Clone and install:**
```bash
git clone <your-repo-url>
cd my-api
pip install poetry
poetry install --no-root
```

2. **Setup database:**
```bash
createdb mydatabase
cp .env.example .env
# Edit .env with your database credentials
```

3. **Create your first API:**
```bash
python cli.py full blog Post -f "title:str,content:str,author:str"
```

4. **Run the server:**
```bash
poetry run fastapi dev src/main.py --host 0.0.0.0 
```

Visit **http://localhost:8000/docs** to see your auto-generated API documentation!

## 📖 CLI Usage

### Generate Complete Apps

```bash
# Create a blog app with Post model
python cli.py full blog Post -f "title:str,content:str,author:str"

# Add more models to existing app
python cli.py model blog Comment -f "content:str,post_id:int,author:str"
python cli.py model blog Category -f "name:str,description:str"
```

### Step-by-Step Creation

```bash
# Create app structure first
python cli.py app_create blog

# Then add models
python cli.py model blog Post -f "title:str,content:str"
```

### List Existing Apps

```bash
python cli.py list_apps
```

## 🎯 Generated API Endpoints

Each model automatically gets these REST endpoints:

| Method | Endpoint | Description | Example |
|--------|-----------|-------------|---------|
| `GET` | `/{models}` | List items (paginated) | `GET /api/v1/posts` |
| `GET` | `/{models}/{id}` | Get item by ID | `GET /api/v1/posts/1` |
| `POST` | `/{models}` | Create new item | `POST /api/v1/posts` |
| `PUT` | `/{models}/{id}` | Update item | `PUT /api/v1/posts/1` |
| `DELETE` | `/{models}/{id}` | Soft delete | `DELETE /api/v1/posts/1` |
| `PATCH` | `/{models}/{id}/restore` | Restore item | `PATCH /api/v1/posts/1/restore` |
| `DELETE` | `/{models}/{id}/force` | Permanent delete | `DELETE /api/v1/posts/1/force` |

## 💡 Example Usage

### Create a Post
```bash
curl -X POST "http://localhost:8000/api/v1/posts" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "This is the content",
    "author": "John Doe"
  }'
```

### List Posts with Pagination
```bash
curl "http://localhost:8000/api/v1/posts?page=1&per_page=10"
```

### Update a Post
```bash
curl -X PUT "http://localhost:8000/api/v1/posts/1" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated Title"}'
```

## 🏗️ Project Structure

```
src/
├── core/                    # Framework core
│   ├── bases/              # Base classes (Repository, Service, Router)
│   ├── database.py         # DB configuration & models
│   ├── exceptions.py       # Custom exceptions
│   └── cli.py             # Code generator CLI
└── apps/                   # Your business apps
    └── blog/
        ├── models/         # SQLModel classes
        ├── repositories/   # Data access layer
        ├── services/       # Business logic
        ├── routers/        # API routes
        └── schemas/        # Pydantic schemas
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mydatabase
SECRET_KEY=your-super-secret-key
ENVIRONMENT=development
DEBUG=True
```

### Custom Model Example
```python
from src.core.database import BaseModel
from sqlmodel import Field

class Post(BaseModel, table=True):
    __tablename__ = "blog_posts"
    
    title: str = Field()
    content: str = Field()
    author: str = Field()
```

### Custom Business Logic
```python
class PostService(BaseService[Post]):
    async def _validate_create(self, create_data: Dict[str, Any]) -> None:
        if len(create_data.get('title', '')) < 5:
            raise ValidationException("Title must be at least 5 characters")
```

## 🛠️ Development

### Running the Server
```bash
# Development with auto-reload
python main.py

# Or using uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc  
- **Health Check**: http://localhost:8000/health

## 🚀 Deployment

### Production Setup
```bash
# Update environment
ENVIRONMENT=production
DEBUG=False

# Run with production settings
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Example
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🔧 Troubleshooting

### Common Issues

**Table doesn't exist error:**
- Ensure models are imported in `database.py`
- Restart server after creating new models

**Database connection issues:**
- Verify PostgreSQL is running
- Check DATABASE_URL in .env file

**Import errors:**
- Check Python path and module structure
- Verify all `__init__.py` files exist

## 🤝 Contributing

We welcome contributions! Please feel free to submit pull requests or open issues for bugs and feature requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [SQLModel](https://sqlmodel.tiangolo.com/) for the great ORM
- [Typer](https://typer.tiangolo.com/) for the CLI framework

---

**⭐ Star this repo if you find it helpful!**

---

<div align="center">

### Built with ❤️ using FastAPI and SQLModel

<!-- [**Documentation**](#) • [**Examples**](#) • [**Report Bug**](#) • [**Request Feature**](#) -->

</div>