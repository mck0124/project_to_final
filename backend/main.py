from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_302_FOUND

from backend.database import SessionLocal
from backend.models import User, Candidate, MailLog
from backend.utils import verify_password

app = FastAPI()

# 템플릿과 정적 파일 폴더 설정
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend/templates")

# 홈(랜딩) 페이지
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 로그인 페이지
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 로그인 처리
@app.post("/login")
async def login_process(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()
    if user and verify_password(password, user.password_hash):
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

# 대시보드 페이지
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# 후보자 리스트
@app.get("/candidates", response_class=HTMLResponse)
async def candidate_list(request: Request):
    db = SessionLocal()
    candidates = db.query(Candidate).all()
    db.close()
    return templates.TemplateResponse("candidates.html", {
        "request": request,
        "candidates": candidates
    })

# 메일 발송 처리
@app.post("/send-mail")
async def send_mail(request: Request, candidate_ids: list[int] = Form(...)):
    db = SessionLocal()
    for cid in candidate_ids:
        mail = MailLog(
            company_id=1,  # TODO: 실제 로그인된 기업 ID로 교체
            candidate_id=cid,
            status="sent"
        )
        db.add(mail)
    db.commit()
    db.close()
    return RedirectResponse(url="/candidates", status_code=HTTP_302_FOUND)

# 회신자 리스트
@app.get("/replied-candidates", response_class=HTMLResponse)
async def replied_candidates(request: Request):
    db = SessionLocal()
    replied = db.query(MailLog).filter(MailLog.status == "replied").all()
    candidate_ids = [r.candidate_id for r in replied]
    candidates = db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
    db.close()
    return templates.TemplateResponse("replied_candidates.html", {
        "request": request,
        "replied_candidates": candidates
    })
