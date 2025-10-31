/**
 * Lambda@Edge Function for Low-Latency Audio Matching
 * 
 * This function provides quick preliminary matching at edge locations
 * before forwarding to origin for detailed processing.
 */

'use strict';

exports.handler = async (event, context) => {
    const request = event.Records[0].cf.request;
    const response = event.Records[0].cf.response;
    
    // Process origin response
    if (response) {
        return processOriginResponse(response, request);
    }
    
    // Process viewer request
    return processViewerRequest(request);
};

/**
 * Process viewer request (before reaching origin)
 */
function processViewerRequest(request) {
    // Add edge processing metadata
    request.headers['x-edge-processing'] = [{
        key: 'X-Edge-Processing',
        value: 'enabled'
    }];
    
    // Add request timestamp for latency measurement
    request.headers['x-edge-start-time'] = [{
        key: 'X-Edge-Start-Time',
        value: Date.now().toString()
    }];
    
    // Optimize request routing based on payload size
    const contentLength = request.headers['content-length'] ? 
        parseInt(request.headers['content-length'][0].value) : 0;
    
    if (contentLength > 1048576) { // > 1MB
        // Route large requests to specific origin path
        request.headers['x-large-payload'] = [{
            key: 'X-Large-Payload',
            value: 'true'
        }];
    }
    
    return request;
}

/**
 * Process origin response (before sending to viewer)
 */
function processOriginResponse(response, request) {
    // Calculate edge processing latency
    const startTime = request.headers['x-edge-start-time'] ?
        parseInt(request.headers['x-edge-start-time'][0].value) : Date.now();
    const latency = Date.now() - startTime;
    
    // Add latency header for monitoring
    response.headers['x-edge-latency'] = [{
        key: 'X-Edge-Latency',
        value: latency.toString()
    }];
    
    // Add cache control based on response status
    if (response.status === '200') {
        // Cache successful matches for 30 minutes
        response.headers['cache-control'] = [{
            key: 'Cache-Control',
            value: 'public, max-age=1800, s-maxage=1800'
        }];
    } else if (response.status === '404') {
        // Cache not-found responses for 5 minutes
        response.headers['cache-control'] = [{
            key: 'Cache-Control',
            value: 'public, max-age=300, s-maxage=300'
        }];
    }
    
    // Security headers
    response.headers['x-content-type-options'] = [{
        key: 'X-Content-Type-Options',
        value: 'nosniff'
    }];
    
    response.headers['x-frame-options'] = [{
        key: 'X-Frame-Options',
        value: 'DENY'
    }];
    
    return response;
}
