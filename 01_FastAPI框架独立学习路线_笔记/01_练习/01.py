from fastapi import FastAPI

app = FastAPI(title="TaskHub API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/tasks")
def list_tasks():
    return [
        {
            "id": 1,
            "title": "学习 FastAPI",
            "status": "todo",
        }
    ]


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    return {
        "id": task_id,
        "title": "学习 FastAPI",
        "status": "todo",
    }

@app.get("/tasks")
def list_tasks(page: int = 1, page_size: int = 20):
    return {
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": 1,
                "title": "学习 FastAPI",
                "status": "todo",
            }
        ],
    }