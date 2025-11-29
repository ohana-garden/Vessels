@echo off
echo === Vessels Repository Cleanup ===
echo.

cd /d "%~dp0"

echo Step 1: Merging cleanup into main...
git checkout main
git pull origin main
git merge origin/claude/implement-vessels-ssf-01B3mCgidJh7Vedr8Hd6nz4Y -m "Merge cleanup: remove obsolete files"
git push origin main
echo.

echo Step 2: Deleting stale branches...
for %%b in (
  "claude/add-agent-kuleana-011CV33bJXZAZqpu89JYpmFQ"
  "claude/add-commercial-fee-structure-01N296EbTnuaL9orrRcHcNEh"
  "claude/add-external-wisdom-01KsTqifp1g5hTJm5sNFc5Av"
  "claude/add-falkordb-integration-012nxb6WEUuxQGLuJhNF4LX9"
  "claude/add-payment-frameworks-01LCnfhZYvwGWofACjtkdmwD"
  "claude/add-volunteer-info-readme-011VvUXp9t3pNXgcSgZBWEHF"
  "claude/agent-zero-core-init-01JhwBYRj5pxJNtvozHHsbqC"
  "claude/agent-zero-refactor-01NLrnKgNTKHm1bqtAN68AnG"
  "claude/analyze-shoghi-write-readme-01XnhSrAEVFkKUMxDHufCFG6"
  "claude/assess-codebase-status-01CCxTeVgSU5tVcjuUS3NhFN"
  "claude/bahai-moral-manifold-01Jf8LJ3P3z95N19DXhzPeyM"
  "claude/bmad-code-review-01Fw8mQSoH7pEb1HN7oj9nDz"
  "claude/chatgpt5-c-011CV3goFUejuuG3Nbn7zuYn"
  "claude/clarify-task-01CFKPUstnSk4grZkr1uoiUV"
  "claude/code-review-fixes-01PZHJWtb1nyxHxs7BRUfd7w"
  "claude/codex-integration-setup-01SfJUi7ePiVNPjXFz9cTLxA"
  "claude/complete-missing-details-01FQucaR53j6gHN2WnuwT3Rk"
  "claude/continue-work-01XVzdAnW71gUbAoRuqE1BSr"
  "claude/create-shoghi-replicant-repo-01LtFtEEvgCxZR1V5tPJTVmN"
  "claude/define-customer-needs-01MC2WZdta79hituswX2LhPX"
  "claude/delete-md-files-013Ks8Ktny7MXEaY9QwWCBZr"
  "claude/delete-unused-code-0178gJWR5HeRmJSL9CkW88Uy"
  "claude/determine-next-steps-01U2stHe1fxQsmKxA5gZ6Nzm"
  "claude/digital-twin-personification-01Si5wr9roMLCcHKQywoT4Ti"
  "claude/docker-vessels-container-016bqbHpkVbGGmZ5iaaEkSPP"
  "claude/docker-vessels-windows-013sakxqx8KNXXgYtgeEXeHL"
  "claude/ethical-agents-framework-011Y3LnSJPgYK1s6Ek7NPQer"
  "claude/externalize-secrets-01RM5jqSFbJcum5zoi4BpG6C"
  "claude/fix-architecture-code-01ENfGdvRaxQjHpmfSfRyVds"
  "claude/fix-critical-architecture-01UWgH9Gb5Psbp43V6vCZNFN"
  "claude/fix-docker-dependencies-01SyMphbmh97spGACUCo3XxT"
  "claude/fix-dockerfile-docs-copy-01212NwQJ5iPckfyr6LSYV3x"
  "claude/fix-file-replacement-01GYu7bWnLg2AhvU53zQmQDT"
  "claude/fix-security-backdoor-017xDFuYRHjdMgedSHWpdwo3"
  "claude/fix-setup-web-file-01VUsDczCo9zruMRmGHNAFTb"
  "claude/fix-system-interface-019zUidzjAKozThzYkazUqVe"
  "claude/fix-vessels-registry-013xEc2UsEt8zQXBMX8oVWFs"
  "claude/grants-are-01CZb1V28vexTWUJduykRUYz"
  "claude/implement-bmad-improvements-015JrtRYYEgJFXhuSUna3nhb"
  "claude/implement-phase-2-012dCbM1o2PFPDZk6HbjTPwV"
  "claude/implement-ten-framework-01RdLZd5xuj9Q5uztkmXFcgv"
  "claude/implement-vessels-ssf-01BJ7aRKaWnupk53y4kc6igb"
  "claude/implement-vessels-ssf-01B3mCgidJh7Vedr8Hd6nz4Y"
  "claude/improve-content-generator-01RP7uPD9aWiB3D5LSCtwqK6"
  "claude/improve-vessel-ux-01NMzxRZJcCpFB8cVPzHBbGs"
  "claude/improve-vessels-architecture-01HcTS8oa6EBT35oYgAHyF9G"
  "claude/integrate-falkordb-01MfhcmN5T7djSPHRUYzhU5g"
  "claude/integrate-teachable-moments-01BYuQ87XMEs46us3UZXkGHs"
  "claude/kala-dollar-peg-01JfkYFMkCMPY6PjViFRVfBz"
  "claude/merge-all-to-main-011VvUXp9t3pNXgcSgZBWEHF"
  "claude/merge-shoghi-to-main-01Tp17k7pZBuH4wkzuV9oK2y"
  "claude/multi-class-agent-architecture-01WkxmS52xch473xmUh8NGTE"
  "claude/neighborhood-payment-platform-01QyuhvsKDdsoJYTMeVdX1Mk"
  "claude/optimize-persona-schema-012eUUKZUrQiDhFiVRuCx1Kt"
  "claude/parable-browser-agent-015Ze7YpkaEWVdBs8a9gX115"
  "claude/refactor-architecture-01QWyDQyVfHUHQ7yGcN3YAyF"
  "claude/refactor-component-a-01TpMRUcUsgins8cc7MRH2Vh"
  "claude/refactor-vessel-ux-01J6jhU1zvCso8xbfNhb3bVE"
  "claude/rename-shoghi-to-vessels-0177X1ckakrhhG628ZFr5zge"
  "claude/rename-shoghi-to-vessels-01Cnve5BVUcc5aNEFUhK2ScW"
  "claude/replace-critical-components-01XuH4eBDHgoQaXo9vKbiU92"
  "claude/review-and-apply-updates-01AV7YpEZPjqwnAYkmPabfK1"
  "claude/review-chat-ux-01GTM2BDqEuhWfpkgo9g7r9K"
  "claude/review-constraint-spec-01Fmsk9H6N5iLWXVozpp1SEA"
  "claude/rewrite-readme-shoghi-015DMDWjrS7FWnXQmiZzu4Rg"
  "claude/rewrite-readme-vonnegut-01F8W2gaWnLdqmbdH4pUC9Sa"
  "claude/setup-quadratic-funding-tracker-01Xr4rXCTSj3VcdQ8hNijTQF"
  "claude/shoghi-agent-zero-integration-01CKt7Riz5bqksCBVaz4xsUa"
  "claude/shoghi-moral-constraints-01Tp17k7pZBuH4wkzuV9oK2y"
  "claude/shoghi-projects-graphiti-019iQeHcnd9ApgLsZ8bM1rXz"
  "claude/vessels-codebase-review-011jyoPnyXAjAimgvhSBQK8f"
  "claude/vessels-codex-framework-01RfNhZexvurQv8VtXsLSZZB"
  "claude/vessels-improvements-019JCJT7V71q26jAqWK15WVf"
  "claude/vessels-platform-restoration-018xuR86jxGpKnWvwPKvSTsf"
  "claude/whats-goin-011CV4ojerXR1KgPQZLawAoA"
  "codex/add-vessel-abstraction-and-management"
  "codex/fix-codex-review-issues-in-pr-#14"
  "codex/review-code-for-optimization-suggestions"
  "codex/review-codebase-and-suggest-improvements"
  "codex/review-codebase-and-suggest-improvements-eohjg6"
  "codex/review-repo-for-bmad-compliance"
  "merge/all-into-main"
) do (
  echo   Deleting %%~b...
  git push origin --delete %%~b 2>nul
)

echo.
echo === Cleanup Complete ===
echo.
git branch -r
echo.
pause
