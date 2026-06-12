/**
 * Transform response from OpenAI-compatible API to extract message content.
 *
 * This function handles common error cases and extracts the content from
 * the standard OpenAI chat completion response format.
 *
 * @param {Object} json - Parsed JSON response
 * @param {string} text - Raw response text
 * @param {Object} context - Request context including response status
 * @returns {string|Object} - Extracted content or error object
 */
module.exports = (json, text, context) => {
  // Check HTTP status
  if (context.response.status !== 200) {
    return {
      error: `HTTP ${context.response.status}: ${text || 'No response'}`
    };
  }

  // Check if JSON was parsed successfully
  if (!json) {
    return {
      error: 'Invalid JSON response',
      raw: text
    };
  }

  // Extract content from OpenAI-compatible response format
  const content = json.choices?.[0]?.message?.content;

  if (content === undefined || content === null) {
    return {
      error: 'Unexpected response format',
      raw: json
    };
  }

  return content;
};