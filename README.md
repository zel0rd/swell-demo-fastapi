# PADO Write · FastAPI

PADO Write는 **FastAPI**로 만든 반응형 글쓰기 작업 공간입니다. 문서 작성, 브라우저 초안 저장, 집중 모드, 텍스트 내보내기와 실제 서버 기반 글 분석을 제공합니다. 초안은 localStorage에 저장되어 다른 기기와 동기화되지 않습니다. 분석 시 본문은 서버로 전송되지만 저장하거나 외부 서비스로 보내지 않습니다. DB, 로그인, 외부 API 키 없이 Swell에 배포할 수 있습니다.

- `/`: 문서 편집기 · 브라우저 저장 · 집중 모드 · TXT 내보내기
- `POST /api/analyze`: 최대 20,000자 본문의 단어/문장/문단 수, 반복 단어, 예상 읽기 시간 분석. 빈 글은 거부하며 읽기 시간은 분당 240단어 기준의 추정치입니다.
- `/health`: HTTP 200 + `{"status":"ok", ...}`
- `/api/info`: 공개용 앱 버전/지역 정보 (환경 전체를 노출하지 않음)
- `/api/hello?name=파도`: 한글 이름 인사 API
- `/api/echo`: JSON POST 요청/응답 (메모리나 DB에 저장하지 않음)
- `/docs`, `/openapi.json`: Swagger UI와 OpenAPI 문서 (Swagger UI 자산은 외부 CDN 사용)

## 로컬 실행

필수: Python 3.13 또는 Docker.

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
python -m app.main
```

Tests:

```bash
python -m pytest -q
```

웹사이트: http://localhost:8080

`env.example`은 변수 참고용입니다. Python 실행은 .env 파일을 자동으로 읽지 않습니다. 셸에서 export하거나 Docker --env-file을 사용하세요.
`APP_NAME`, `APP_VERSION`, `DEMO_REGION`은 공개 표시용 값입니다. 여기에 비밀 값을 넣지 마세요. 기본 포트는 `8080`; 컨테이너는 런타임 `PORT`를 따릅니다.

## Docker 실행

```bash
docker build -t swell-demo-fastapi:local .
docker run --rm --name swell-demo-fastapi -p 127.0.0.1:8080:8080 \
  --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges \
  -e APP_VERSION=1.0.0 -e DEMO_REGION=local swell-demo-fastapi:local
```

이미지는 non-root 사용자로 실행됩니다. 바인딩은 `0.0.0.0:8080`, 헬스체크는 `/health`입니다. Dockerfile 기본 이미지는 digest로 고정했고 의존성 lock 파일을 포함했습니다.

### Snap Docker 실행 참고

Snap으로 설치한 Docker에서는 `no-new-privileges`가 컨테이너 시작을 차단하는 [알려진 제약](https://github.com/canonical/docker-snap/blob/main/README.md)이 있습니다. 이 문제가 발생하는 로컬 개발 환경에서는 위 예제의 `--security-opt no-new-privileges`만 생략할 수 있습니다. non-root, read-only, cap-drop은 유지합니다. 일반 Docker 환경과 GitHub CI에서는 원래 옵션을 유지합니다. 호스트의 보안 설정을 변경할 필요는 없습니다.

## swell에 Git 소스로 등록

- 저장소: `https://github.com/zel0rd/swell-demo-fastapi.git`
- 브랜치: `main` (비워두면 `main`, 지정하면 해당 브랜치의 최신 커밋)
- Dockerfile / build context: 루트의 `Dockerfile` / `.`
- 포트: `8080`
- 헬스체크: `/health`
- 권장 시작값: replicas `1`, CPU `250m`, memory `256Mi`

```bash
git rev-parse HEAD
```

아래는 swell 앱 생성 요청의 `spec` 예시입니다. 배포 요청마다 해당 브랜치의 최신 커밋을 조회하며, 동일 배포의 재시도는 조회한 커밋을 유지합니다.

```json
{
  "gitUrl": "https://github.com/zel0rd/swell-demo-fastapi.git",
  "branch": "main",
  "port": 8080,
  "replicas": 1,
  "cpuMillis": 250,
  "memoryMB": 256,
  "healthPath": "/health"
}
```

**현재 swell의 Git 빌드에는 별도 BuildKit/registry/Trivy/Cosign 도구 설정이 필요합니다.** 저장소 등록만으로 해당 인프라가 준비되지는 않습니다. `platform.yaml`은 설정 참고용이며 현재 swell은 이 파일을 자동으로 읽지 않습니다.

## Git 빌더 없이 현재 로컬 swell에서 테스트

swell 개발 환경의 로컬 registry(`localhost:15000`)와 kind runtime이 준비되어 있을 때:

```bash
docker build -t localhost:15000/swell-demo-fastapi:v1 .
docker push localhost:15000/swell-demo-fastapi:v1
docker inspect localhost:15000/swell-demo-fastapi:v1 --format '{{index .RepoDigests 0}}'
```

출력된 `localhost:15000/swell-demo-fastapi@sha256:...`를 대시보드 앱 생성의 **Image**에 입력합니다. 포트 `8080`, 헬스체크 `/health`, replicas `1`로 설정하고 배포하세요. 이미지 방식에서는 `gitUrl`/`branch`을 함께 입력하지 않습니다. 플랫폼 worker의 `TRUSTED_REGISTRIES`와 kind의 registry 접근은 swell README의 로컬 설정을 따라야 합니다.

`localhost:15000`은 로컬 개발 예시입니다. 원격 환경에서는 노드에서 접근 가능한 registry를 사용하세요.

```bash
curl --cacert /path/to/swell/.local/pki/ca.crt \
  --resolve YOUR-SLUG.apps.swell.test:14443:127.0.0.1 \
  https://YOUR-SLUG.apps.swell.test:14443/health
```

브라우저로 접속하려면 해당 호스트의 DNS/hosts 설정과 개발 CA 신뢰 설정이 필요합니다. 공개 GitHub 저장소 생성 자체는 웹사이트 호스팅을 만들지 않습니다.

## 재배포 확인

`/api/info`의 기본 버전 또는 화면 문구를 수정해 새 커밋/이미지 digest로 다시 배포하세요. 페이지와 API 결과가 바뀌는지, 이전 배포로 rollback이 되는지 확인할 수 있습니다. `APP_VERSION`/`DEMO_REGION`은 직접 Docker 실행에서 테스트할 수 있으며 swell의 일반 환경변수 편집 UI/API는 아직 구현되지 않았습니다.

## CI

GitHub Actions에서 pytest, non-root Docker 실행과 HTTP smoke test를 수행합니다. 클라우드 서비스나 registry로 이미지를 자동 배포하지 않습니다.

MIT License.

`swell` 소스 검사는 `.env*` 파일을 차단하므로 변수 예시는 `env.example`이라는 이름을 사용합니다.

Git 배포 후 `/api/info`의 `sourceCommit`과 Swell 배포 기록의 커밋을 비교할 수 있습니다. Swell이 `SWELL_COMMIT_SHA` 빌드 인자를 전달하며, 직접 빌드할 때 생략하면 `unknown`입니다. Git push만으로 자동 배포되지는 않습니다. Swell에서 **배포**를 눌러 새 배포를 요청하세요.
