function isSafeRedirectPath(path) {
  return (
    typeof path === "string" &&
    path.startsWith("/") &&
    !path.startsWith("//") &&
    !path.includes("://")
  );
}

export function getRedirectPathFrom409(error) {
  if (!error?.response || error.response.status !== 409) {
    return null;
  }
  const detail = error.response?.data?.detail;
  if (detail && typeof detail === "object" && typeof detail.redirect_path === "string") {
    const path = detail.redirect_path;
    return isSafeRedirectPath(path) ? path : null;
  }
  return null;
}
