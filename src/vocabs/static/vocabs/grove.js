// from https://www.geeksforgeeks.org/how-to-parse-http-cookie-header-and-return-an-object-of-all-cookie-name-value-pairs-in-javascript/
function cookieParser(cookieString) {
// Return an empty object if cookieString
// is empty
if (cookieString === "")
  return {};

// Get each individual key-value pairs
// from the cookie string
// This returns a new array
let pairs = cookieString.split(";");

// Separate keys from values in each pair string
// Returns a new array which looks like
// [[key1,value1], [key2,value2], ...]
let splitPairs = pairs.map(cookie => cookie.split("="));

// Create an object with all key-value pairs
const cookieObj = splitPairs.reduce(function (obj, cookie) {
  // cookie[0] is the key of cookie
  // cookie[1] is the value of the cookie
  // decodeURIComponent() decodes the cookie
  // string, to handle cookies with special
  // characters, e.g. '$'.
  // string.trim() trims the blank spaces
  // around the key and value.
  obj[decodeURIComponent(cookie[0].trim())] = decodeURIComponent(cookie[1].trim());
  return obj;
}, {})

return cookieObj;
}
