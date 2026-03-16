from __future__ import annotations

from typing import Any, Generator, Optional

import gitlab
from gitlab.exceptions import GitlabError

from core.config import get_config


def _get_client() -> gitlab.Gitlab:
    cfg = get_config()
    gl = gitlab.Gitlab(cfg.gitlab_url, private_token=cfg.gitlab_token)
    try:
        gl.auth()
    except GitlabError as e:
        raise ConnectionError(f"GitLab 인증 실패: {e}") from e
    return gl


def _project(gl: gitlab.Gitlab, name: str):
    """프로젝트 이름 또는 namespace/name으로 프로젝트 객체 반환."""
    try:
        # namespace/name 형태 또는 프로젝트 경로로 검색
        return gl.projects.get(name)
    except GitlabError:
        # 이름으로 검색 fallback
        results = gl.projects.list(search=name, as_list=True)
        if not results:
            raise ValueError(f"프로젝트를 찾을 수 없습니다: {name}")
        return results[0]


# ──────────────────────────── Issues ────────────────────────────

def list_issues(
    project: Optional[str] = None,
    state: str = "open",
    assignee: Optional[str] = None,
) -> list[dict[str, Any]]:
    gl = _get_client()
    kwargs: dict[str, Any] = {"as_list": False}
    if state != "all":
        kwargs["state"] = state
    if assignee:
        kwargs["assignee_username"] = assignee

    try:
        if project:
            proj = _project(gl, project)
            items = proj.issues.list(**kwargs)
        else:
            items = gl.issues.list(**kwargs)

        return [
            {
                "id": i.iid,
                "project": getattr(i, "references", {}).get("full", ""),
                "title": i.title,
                "state": i.state,
                "assignees": ", ".join(a["username"] for a in (i.assignees or [])),
                "created_at": i.created_at[:10],
                "updated_at": i.updated_at[:10],
                "url": i.web_url,
            }
            for i in items
        ]
    except GitlabError as e:
        raise RuntimeError(f"이슈 조회 실패: {e}") from e


# ──────────────────────────── Merge Requests ────────────────────────────

def list_mrs(
    project: Optional[str] = None,
    state: str = "open",
    created_after: Optional[str] = None,
) -> list[dict[str, Any]]:
    gl = _get_client()
    kwargs: dict[str, Any] = {"as_list": False}
    if state != "all":
        kwargs["state"] = state
    if created_after:
        kwargs["created_after"] = f"{created_after}T00:00:00Z"

    try:
        if project:
            proj = _project(gl, project)
            items = proj.mergerequests.list(**kwargs)
        else:
            items = gl.mergerequests.list(**kwargs)

        return [
            {
                "id": m.iid,
                "project": getattr(m, "references", {}).get("full", ""),
                "title": m.title,
                "state": m.state,
                "author": m.author["username"],
                "source_branch": m.source_branch,
                "target_branch": m.target_branch,
                "created_at": m.created_at[:10],
                "url": m.web_url,
            }
            for m in items
        ]
    except GitlabError as e:
        raise RuntimeError(f"MR 조회 실패: {e}") from e


# ──────────────────────────── Pipelines ────────────────────────────

def list_pipelines(
    project: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    gl = _get_client()
    kwargs: dict[str, Any] = {"as_list": False}
    if status:
        kwargs["status"] = status

    try:
        if project:
            proj = _project(gl, project)
            items = proj.pipelines.list(**kwargs)
        else:
            # 전체 프로젝트 파이프라인은 프로젝트 단위로만 가능
            # 프로젝트 없으면 접근 가능한 프로젝트 전체를 순회
            results = []
            for proj in gl.projects.list(membership=True, as_list=False):
                p_kwargs = dict(kwargs)
                results.extend(proj.pipelines.list(**p_kwargs))
            return [_pipeline_row(p) for p in results]

        return [_pipeline_row(p) for p in items]
    except GitlabError as e:
        raise RuntimeError(f"파이프라인 조회 실패: {e}") from e


def _pipeline_row(p) -> dict[str, Any]:
    return {
        "id": p.id,
        "status": p.status,
        "ref": p.ref,
        "sha": p.sha[:8],
        "created_at": p.created_at[:10],
        "url": p.web_url,
    }


# ──────────────────────────── Users ────────────────────────────

def list_users(
    active: bool = False,
    blocked: bool = False,
) -> list[dict[str, Any]]:
    gl = _get_client()
    kwargs: dict[str, Any] = {"as_list": False}
    if active:
        kwargs["active"] = True
    if blocked:
        kwargs["blocked"] = True

    try:
        items = gl.users.list(**kwargs)
        return [
            {
                "id": u.id,
                "username": u.username,
                "name": u.name,
                "email": getattr(u, "email", ""),
                "state": u.state,
                "created_at": u.created_at[:10],
            }
            for u in items
        ]
    except GitlabError as e:
        raise RuntimeError(f"유저 조회 실패: {e}") from e


# ──────────────────────────── Projects ────────────────────────────

def list_projects(
    owned: bool = False,
    starred: bool = False,
) -> list[dict[str, Any]]:
    gl = _get_client()
    kwargs: dict[str, Any] = {"as_list": False}
    if owned:
        kwargs["owned"] = True
    if starred:
        kwargs["starred"] = True

    try:
        items = gl.projects.list(**kwargs)
        return [
            {
                "id": p.id,
                "name": p.path_with_namespace,
                "description": (p.description or "")[:60],
                "visibility": p.visibility,
                "stars": p.star_count,
                "forks": p.forks_count,
                "last_activity": p.last_activity_at[:10],
                "url": p.web_url,
            }
            for p in items
        ]
    except GitlabError as e:
        raise RuntimeError(f"프로젝트 조회 실패: {e}") from e


# ──────────────────────────── Search ────────────────────────────

def search(query: str, scope: str = "projects") -> list[dict[str, Any]]:
    gl = _get_client()
    valid_scopes = {"issues", "merge_requests", "projects", "users", "blobs", "commits"}
    # CLI 표기를 API 표기로 변환
    scope_map = {"mrs": "merge_requests"}
    scope = scope_map.get(scope, scope)
    if scope not in valid_scopes:
        raise ValueError(f"지원하지 않는 scope: {scope}. 허용: {', '.join(valid_scopes)}")

    try:
        items = gl.search(scope, query)
        return list(items)
    except GitlabError as e:
        raise RuntimeError(f"검색 실패: {e}") from e
