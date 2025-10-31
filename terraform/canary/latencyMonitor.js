/**
 * CloudWatch Synthetics Canary for Regional Latency Monitoring
 * 
 * This canary tests API latency from different regions and reports metrics.
 */

const synthetics = require('Synthetics');
const log = require('SyntheticsLogger');
const https = require('https');
const http = require('http');

const apiEndpoint = process.env.API_ENDPOINT || 'https://api.soundhash.io';
const region = process.env.REGION || 'unknown';
const thresholdMs = parseInt(process.env.THRESHOLD_MS || '500');

const handler = async () => {
    // Configure request
    const url = new URL(`${apiEndpoint}/health`);
    const options = {
        hostname: url.hostname,
        port: url.port || (url.protocol === 'https:' ? 443 : 80),
        path: url.pathname,
        method: 'GET',
        headers: {
            'User-Agent': `CloudWatch-Synthetics-Canary-${region}`
        }
    };

    log.info(`Testing latency for ${apiEndpoint} from region ${region}`);

    // Measure latency
    const startTime = Date.now();
    
    return new Promise((resolve, reject) => {
        const client = url.protocol === 'https:' ? https : http;
        
        const req = client.request(options, (res) => {
            const latency = Date.now() - startTime;
            
            log.info(`Response received: status=${res.statusCode}, latency=${latency}ms`);
            
            // Read response body
            let data = '';
            res.on('data', chunk => {
                data += chunk;
            });
            
            res.on('end', () => {
                // Check if latency exceeds threshold
                if (latency > thresholdMs) {
                    log.warn(`High latency detected: ${latency}ms (threshold: ${thresholdMs}ms)`);
                }
                
                // Check response status
                if (res.statusCode >= 200 && res.statusCode < 300) {
                    log.info(`Health check passed for region ${region}`);
                    
                    // Report custom metrics
                    synthetics.addUserAgent(res.headers['user-agent'] || 'unknown');
                    
                    resolve({
                        statusCode: res.statusCode,
                        latency: latency,
                        region: region,
                        healthy: true
                    });
                } else {
                    const error = `Health check failed with status ${res.statusCode}`;
                    log.error(error);
                    reject(new Error(error));
                }
            });
        });
        
        req.on('error', (error) => {
            const latency = Date.now() - startTime;
            log.error(`Request failed after ${latency}ms: ${error.message}`);
            reject(error);
        });
        
        // Set timeout
        req.setTimeout(10000, () => {
            req.destroy();
            reject(new Error('Request timeout after 10 seconds'));
        });
        
        req.end();
    });
};

exports.handler = async () => {
    return await synthetics.executeHttpStep('LatencyCheck', handler);
};
