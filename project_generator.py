"""IRIS v7 Project Generator - Scaffolds, Codes, Commits, Deploys"""
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from config import config
from db import db
from tools import tool_registry, ToolResult

class ProjectGenerator:
    """
    Generate complete projects:
    - Next.js + Tailwind + Framer Motion (frontend)
    - Python + FastAPI + SQLAlchemy (backend)
    - Full-stack with both
    - Auto-commit to GitHub
    - Auto-deploy to Vercel
    - Verify everything works
    """

    TEMPLATES = {
        "nextjs": {
            "description": "Next.js 15 with Tailwind CSS and Framer Motion",
            "files": {
                "package.json": """{
  "name": "{{project_name}}",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "framer-motion": "^11.0.0",
    "lucide-react": "^0.400.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^19.0.0",
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^15.0.0"
  }
}""",
                "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#00ff88',
        secondary: '#0088ff',
        dark: '#0a0a1a',
      },
    },
  },
  plugins: [],
}""",
                "postcss.config.js": """module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}""",
                "tsconfig.json": """{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}""",
                "next.config.js": """/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'dist',
}
module.exports = nextConfig""",
                "app/globals.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  background: #0a0a1a;
  color: #e0e0ff;
}""",
                "app/layout.tsx": """export const metadata = {
  title: '{{project_name}}',
  description: 'Built by IRIS for Infinite Vybeflix',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}""",
                "app/page.tsx": """'use client'
import { motion } from 'framer-motion'

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-center"
      >
        <h1 className="text-6xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
          {{project_name}}
        </h1>
        <p className="mt-4 text-xl text-gray-400">
          Built by IRIS for Infinite Vybeflix
        </p>
      </motion.div>
    </main>
  )
}""",
                "vercel.json": """{
  "version": 2,
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "nextjs"
}"""
            }
        },
        "fastapi": {
            "description": "Python FastAPI with SQLAlchemy and Pydantic",
            "files": {
                "requirements.txt": """fastapi==0.115.0
uvicorn==0.32.0
sqlalchemy==2.0.36
pydantic==2.9.0
python-dotenv==1.0.1
httpx==0.27.0
pytest==8.3.0
""",
                "main.py": """from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from database import engine, Base
from routers import items

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="{{project_name}}",
    description="Built by IRIS for Infinite Vybeflix",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router, prefix="/api/items", tags=["items"])

@app.get("/")
async def root():
    return {"message": "{{project_name}} API", "built_by": "IRIS"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
""",
                "database.py": """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",
                "models.py": """from sqlalchemy import Column, Integer, String, DateTime, Boolean
from database import Base
from datetime import datetime

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
""",
                "schemas.py": """from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True
""",
                "routers/items.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Item
from schemas import ItemCreate, Item

router = APIRouter()

@router.get("/", response_model=List[Item])
async def get_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Item).offset(skip).limit(limit).all()

@router.post("/", response_model=Item)
async def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/{item_id}", response_model=Item)
async def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
""",
                "vercel.json": """{
  "version": 2,
  "builds": [{"src": "main.py", "use": "@vercel/python"}],
  "routes": [{"src": "/(.*)", "dest": "main.py"}]
}""",
                "README.md": """# {{project_name}}

Built by IRIS for Infinite Vybeflix.

## Setup
```bash
pip install -r requirements.txt
python main.py
```

## API Endpoints
- GET / - Root
- GET /health - Health check
- GET /api/items - List items
- POST /api/items - Create item
- GET /api/items/{id} - Get item
"""
            }
        }
    }

    def __init__(self):
        self.projects_dir = os.path.join(config.DATA_DIR, "projects")
        os.makedirs(self.projects_dir, exist_ok=True)

    def generate_project(self, project_name: str, template: str = "nextjs", 
                         description: str = "") -> Dict:
        """Generate a complete project from template"""

        if template not in self.TEMPLATES:
            return {"success": False, "error": f"Unknown template: {template}"}

        template_data = self.TEMPLATES[template]
        project_dir = os.path.join(self.projects_dir, project_name)

        try:
            # Create project directory
            os.makedirs(project_dir, exist_ok=True)

            # Generate files
            for file_path, content in template_data["files"].items():
                full_path = os.path.join(project_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Replace placeholders
                processed = content.replace("{{project_name}}", project_name)

                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(processed)

            # Save to database
            db.save_memory(
                f"project_{project_name}",
                json.dumps({"name": project_name, "template": template, "path": project_dir}),
                category="project",
                importance=7
            )

            return {
                "success": True,
                "project_name": project_name,
                "template": template,
                "path": project_dir,
                "files_created": len(template_data["files"]),
                "description": template_data["description"]
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def deploy_project(self, project_name: str, repo_name: str = None, 
                      deploy_to_vercel: bool = True) -> Dict:
        """Deploy project to GitHub and optionally Vercel"""
        project_dir = os.path.join(self.projects_dir, project_name)

        if not os.path.exists(project_dir):
            return {"success": False, "error": "Project not found"}

        repo_name = repo_name or project_name
        results = {"github": None, "vercel": None}

        # Create GitHub repo
        try:
            from tools import tool_registry
            repo_result = tool_registry.tools["git_create_repo"](
                name=repo_name,
                description=f"Built by IRIS for Infinite Vybeflix",
                private=False
            )

            if repo_result.success:
                results["github"] = repo_result.data

                # Clone, copy files, commit, push
                clone_result = tool_registry.tools["git_clone"](
                    repo_url=repo_result.data["clone_url"],
                    local_name=repo_name
                )

                if clone_result.success:
                    # Copy project files to repo
                    repo_dir = clone_result.data["path"]
                    for item in os.listdir(project_dir):
                        src = os.path.join(project_dir, item)
                        dst = os.path.join(repo_dir, item)
                        if os.path.isdir(src):
                            shutil.copytree(src, dst, dirs_exist_ok=True)
                        else:
                            shutil.copy2(src, dst)

                    # Commit and push
                    commit_result = tool_registry.tools["git_commit"](
                        repo_path=repo_dir,
                        message="Initial commit - Built by IRIS"
                    )

                    if commit_result.success:
                        push_result = tool_registry.tools["git_push"](
                            repo_path=repo_dir,
                            branch="main"
                        )
                        results["github"]["pushed"] = push_result.success
        except Exception as e:
            results["github_error"] = str(e)

        # Deploy to Vercel
        if deploy_to_vercel:
            try:
                from tools import tool_registry
                vercel_result = tool_registry.tools["vercel_deploy"](
                    project_path=project_dir,
                    project_name=repo_name
                )
                results["vercel"] = vercel_result.data if vercel_result.success else {"error": vercel_result.error}
            except Exception as e:
                results["vercel_error"] = str(e)

        return {
            "success": results["github"] is not None,
            "results": results
        }

    def get_projects(self) -> List[Dict]:
        """List all generated projects"""
        projects = []
        if os.path.exists(self.projects_dir):
            for name in os.listdir(self.projects_dir):
                path = os.path.join(self.projects_dir, name)
                if os.path.isdir(path):
                    projects.append({
                        "name": name,
                        "path": path,
                        "created": datetime.fromtimestamp(os.path.getctime(path)).isoformat()
                    })
        return projects

project_generator = ProjectGenerator()
