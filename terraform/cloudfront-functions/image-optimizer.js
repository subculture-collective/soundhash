/**
 * CloudFront Function for Image Optimization
 * 
 * Features:
 * - WebP conversion support
 * - Automatic image format detection
 * - Query parameter-based resizing
 * - Accept header-based format selection
 */

function handler(event) {
    var request = event.request;
    var uri = request.uri;
    var headers = request.headers;
    
    // Only process image requests
    if (!uri.match(/\.(jpg|jpeg|png|gif|webp)$/i)) {
        return request;
    }
    
    // Check if client supports WebP
    var supportsWebP = false;
    if (headers.accept && headers.accept.value) {
        supportsWebP = headers.accept.value.includes('image/webp');
    }
    
    // Parse query parameters for image transformations
    var params = {};
    if (request.querystring) {
        var pairs = request.querystring.split('&');
        for (var i = 0; i < pairs.length; i++) {
            var pair = pairs[i].split('=');
            if (pair.length === 2) {
                params[pair[0]] = pair[1];
            }
        }
    }
    
    // Build transformation path
    var transformations = [];
    
    // Width transformation
    if (params.w || params.width) {
        transformations.push('w_' + (params.w || params.width));
    }
    
    // Height transformation
    if (params.h || params.height) {
        transformations.push('h_' + (params.h || params.height));
    }
    
    // Quality transformation
    if (params.q || params.quality) {
        transformations.push('q_' + (params.q || params.quality));
    }
    
    // Format transformation - prefer WebP if supported
    var format = params.f || params.format;
    if (!format && supportsWebP && !uri.match(/\.webp$/i)) {
        format = 'webp';
    }
    if (format) {
        transformations.push('f_' + format);
    }
    
    // If transformations are requested, update the URI
    if (transformations.length > 0) {
        var ext = uri.match(/\.[^.]+$/)[0];
        var basePath = uri.substring(0, uri.lastIndexOf(ext));
        var transformPath = transformations.join(',');
        
        // New URI format: /static/images/optimized/w_800,h_600,q_85,f_webp/image.jpg
        request.uri = basePath + '/optimized/' + transformPath + ext;
    }
    
    // Add cache key headers for better cache hit ratio
    if (!request.headers['cloudfront-is-desktop-viewer']) {
        request.headers['cloudfront-is-desktop-viewer'] = { value: 'true' };
    }
    if (!request.headers['cloudfront-is-mobile-viewer']) {
        request.headers['cloudfront-is-mobile-viewer'] = { value: 'false' };
    }
    
    return request;
}
