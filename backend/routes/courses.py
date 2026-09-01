"""Course endpoints (maintainability sequences).

  GET  /courses                     list of courses (public)
  GET  /courses/{slug}              course + ordered steps (public)
  POST /courses/{slug}/complete     record the run's score (auth)
  GET  /courses/{slug}/leaderboard  users ranked by total tokens across the course

A course's step problems are course_only (hidden from GET /problems) but still
loaded individually via GET /problems/{id} by the course runner.

Owner: Supabase person (DESIGN.md §8.1). Thin wrappers over dataaccess/courses.py.
"""

from fastapi import APIRouter, Depends, HTTPException

from dataaccess import courses as courses_dao
from deps import require_profile
from schemas import (
    CourseCompleteRequest,
    CourseCompletionResponse,
    CourseDetail,
    CourseLeaderboardRow,
    CourseSummary,
)

router = APIRouter(tags=["courses"])


@router.get("/courses", response_model=list[CourseSummary])
async def list_courses():
    return courses_dao.list_courses()


@router.get("/courses/{slug}", response_model=CourseDetail)
async def get_course(slug: str):
    course = courses_dao.get_course(slug)
    if course is None:
        raise HTTPException(status_code=404, detail="course not found")
    return course


@router.post("/courses/{slug}/complete", response_model=CourseCompletionResponse)
async def complete_course(slug: str, body: CourseCompleteRequest, user=Depends(require_profile)):
    return courses_dao.record_completion(user["id"], slug, body.submission_ids)


@router.get("/courses/{slug}/leaderboard", response_model=list[CourseLeaderboardRow])
async def get_course_leaderboard(slug: str):
    return courses_dao.course_leaderboard(slug)
