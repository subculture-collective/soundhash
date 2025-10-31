/**
 * Lambda@Edge Function for Fingerprint Lookup Caching
 * 
 * This function runs at CloudFront edge locations to provide
 * low-latency fingerprint lookups with intelligent caching.
 */

'use strict';

const { webcrypto } = require('crypto');

exports.handler = async (event, context) => {
    const request = event.Records[0].cf.request;
    
    // Only process POST requests with body
    if (request.method !== 'POST' || !request.body || !request.body.data) {
        return request;
    }
    
    try {
        // Decode and parse request body
        const bodyData = Buffer.from(request.body.data, 'base64').toString('utf-8');
        const requestPayload = JSON.parse(bodyData);
        
        // Generate cache key from fingerprint data
        const cacheKey = await generateCacheKey(requestPayload);
        
        // Add cache key to headers for origin server
        request.headers['x-fingerprint-cache-key'] = [{
            key: 'X-Fingerprint-Cache-Key',
            value: cacheKey
        }];
        
        // Add timestamp for latency tracking
        request.headers['x-edge-request-time'] = [{
            key: 'X-Edge-Request-Time',
            value: Date.now().toString()
        }];
        
        // Add edge location for regional analytics
        const edgeLocation = event.Records[0].cf.config.distributionId;
        request.headers['x-edge-location'] = [{
            key: 'X-Edge-Location',
            value: edgeLocation
        }];
        
        console.log(`Fingerprint lookup request with cache key: ${cacheKey}`);
        
    } catch (error) {
        console.error('Error processing fingerprint request:', error);
        // Continue with original request on error
    }
    
    return request;
};

/**
 * Generate a deterministic cache key from fingerprint data
 */
async function generateCacheKey(payload) {
    // Extract fingerprint data (adjust based on your fingerprint structure)
    const fingerprintData = payload.fingerprint || payload.fingerprint_hash || '';
    const metadata = payload.metadata || {};
    
    // Create cache key components
    const components = [
        fingerprintData,
        metadata.sample_rate || '',
        metadata.duration || ''
    ].filter(Boolean).join('|');
    
    // Generate hash for cache key using Web Crypto API
    const encoder = new TextEncoder();
    const data = encoder.encode(components);
    const hashBuffer = await webcrypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex.substring(0, 16);
}
