/** Turn an API failure into a short title and message for the page. */

export function describeLoadError(what, error) {
  const detail = (error && error.message) || (typeof error === "string" ? error : "") || "Please try again.";
  if (error?.status === 404) {
    return {
      title: `${what} not found`,
      message: detail,
    };
  }
  if (error?.status === 403) {
    return {
      title: `Cannot load ${what.toLowerCase()}`,
      message: detail,
    };
  }
  return {
    title: `Error fetching ${what.toLowerCase()}`,
    message: detail,
  };
}

export function describeActionError(action, error) {
  const detail = (error && error.message) || (typeof error === "string" ? error : "") || "Please try again.";
  return `${action}: ${detail}`;
}
