export function getRedirectPathFrom409(error) {
  if (!error?.response || error.response.status !== 409) {
    return null;
  }
  const detail = error.response?.data?.detail;
  if (detail && typeof detail === "object" && typeof detail.redirect_path === "string") {
    return detail.redirect_path;
  }
  return null;
}
