/**
 * SoundHash JavaScript Client SDK
 * 
 * Real-time audio streaming client for SoundHash API.
 * Captures audio from browser microphone and streams to server for live matching.
 * 
 * Usage:
 *   const client = new SoundHashClient('wss://api.soundhash.io', 'your-api-key');
 *   
 *   client.onMatch = (matchData) => {
 *     console.log('Match found:', matchData.matches);
 *   };
 *   
 *   await client.connect();
 *   await client.startMicrophone();
 */

class SoundHashClient {
  /**
   * Initialize SoundHash client.
   * 
   * @param {string} apiUrl - WebSocket API URL (e.g., 'wss://api.soundhash.io')
   * @param {string} apiKey - API authentication key
   * @param {string} [clientId] - Unique client identifier (auto-generated if not provided)
   * @param {number} [sampleRate=22050] - Audio sample rate in Hz
   */
  constructor(apiUrl, apiKey, clientId = null, sampleRate = 22050) {
    this.apiUrl = apiUrl.replace('https://', 'wss://').replace('http://', 'ws://');
    this.apiKey = apiKey;
    this.clientId = clientId || this._generateUUID();
    this.sampleRate = sampleRate;
    
    this.ws = null;
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.source = null;
    this._reconnectAttempts = 0;
    this._maxReconnectAttempts = 5;
    this._reconnectDelay = 1000;
  }
  
  /**
   * Generate a UUID v4.
   * @private
   */
  _generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  /**
   * Connect to SoundHash WebSocket.
   * 
   * @returns {Promise<void>}
   */
  async connect() {
    return new Promise((resolve, reject) => {
      const uri = `${this.apiUrl}/ws/stream/${this.clientId}`;
      
      try {
        this.ws = new WebSocket(uri);
        
        this.ws.onopen = () => {
          console.log('Connected to SoundHash');
          this._reconnectAttempts = 0;
          resolve();
        };
        
        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
        
        this.ws.onclose = () => {
          console.log('WebSocket closed');
          this._handleReconnect();
        };
        
        this.ws.onmessage = (event) => {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        };
      } catch (error) {
        reject(error);
      }
    });
  }
  
  /**
   * Handle automatic reconnection.
   * @private
   */
  async _handleReconnect() {
    if (this._reconnectAttempts < this._maxReconnectAttempts) {
      this._reconnectAttempts++;
      const delay = this._reconnectDelay * Math.pow(2, this._reconnectAttempts - 1);
      
      console.log(`Reconnecting in ${delay}ms (attempt ${this._reconnectAttempts}/${this._maxReconnectAttempts})`);
      
      setTimeout(async () => {
        try {
          await this.connect();
          
          // Restart microphone if it was active
          if (this.mediaStream) {
            await this.startMicrophone();
          }
        } catch (error) {
          console.error('Reconnection failed:', error);
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      this.onError('Connection lost and could not reconnect');
    }
  }
  
  /**
   * Start capturing audio from microphone.
   * 
   * @returns {Promise<void>}
   */
  async startMicrophone() {
    try {
      // Request microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.sampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });
      
      // Set up audio processing
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
        sampleRate: this.sampleRate
      });
      
      this.source = this.audioContext.createMediaStreamSource(this.mediaStream);
      
      // Use ScriptProcessorNode for older browsers, AudioWorklet for modern browsers
      if (this.audioContext.audioWorklet) {
        // Modern approach (not implemented here for simplicity)
        // In production, use AudioWorkletProcessor
        this._startWithScriptProcessor();
      } else {
        this._startWithScriptProcessor();
      }
      
      console.log('Microphone started');
    } catch (error) {
      console.error('Failed to start microphone:', error);
      this.onError(`Microphone error: ${error.message}`);
      throw error;
    }
  }
  
  /**
   * Start audio processing with ScriptProcessorNode.
   * @private
   */
  _startWithScriptProcessor() {
    // Create script processor (deprecated but widely supported)
    this.processor = this.audioContext.createScriptProcessor(4096, 1, 1);
    
    this.processor.onaudioprocess = (e) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        const audioData = e.inputBuffer.getChannelData(0);
        this.sendAudioChunk(audioData);
      }
    };
    
    this.source.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
  }
  
  /**
   * Send audio chunk to server.
   * 
   * @param {Float32Array} audioData - Audio data to send
   */
  sendAudioChunk(audioData) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // Convert Float32Array to ArrayBuffer and send
      const buffer = audioData.buffer;
      this.ws.send(buffer);
    }
  }
  
  /**
   * Handle incoming message from server.
   * 
   * @param {object} message - Parsed JSON message
   */
  handleMessage(message) {
    switch (message.type) {
      case 'match':
        this.onMatch(message.data);
        break;
      case 'status':
        this.onStatus(message.message);
        break;
      case 'error':
        this.onError(message.message);
        break;
      default:
        console.warn('Unknown message type:', message.type);
    }
  }
  
  /**
   * Callback for match notifications.
   * Override this method to handle matches.
   * 
   * @param {object} matchData - Match information
   */
  onMatch(matchData) {
    console.log('Match found:', matchData);
  }
  
  /**
   * Callback for status updates.
   * Override this method to handle status updates.
   * 
   * @param {string} status - Status message
   */
  onStatus(status) {
    console.log('Status:', status);
  }
  
  /**
   * Callback for error messages.
   * Override this method to handle errors.
   * 
   * @param {string} errorMessage - Error message
   */
  onError(errorMessage) {
    console.error('Error:', errorMessage);
  }
  
  /**
   * Disconnect and cleanup resources.
   */
  disconnect() {
    // Stop microphone
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    
    // Disconnect audio nodes
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    
    if (this.source) {
      this.source.disconnect();
      this.source = null;
    }
    
    // Close audio context
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }
    
    // Close WebSocket
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    console.log('Disconnected from SoundHash');
  }
}

// Export for CommonJS and ES modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SoundHashClient;
}

// Example usage
if (typeof window !== 'undefined') {
  window.SoundHashClient = SoundHashClient;
  
  // Example initialization (commented out)
  /*
  const client = new SoundHashClient('ws://localhost:8000', 'your-api-key');
  
  client.onMatch = (matchData) => {
    const matches = matchData.matches || [];
    matches.forEach(match => {
      console.log(`🎵 Match: ${match.title} - ${(match.similarity_score * 100).toFixed(1)}%`);
    });
  };
  
  // Connect and start
  async function start() {
    try {
      await client.connect();
      await client.startMicrophone();
    } catch (error) {
      console.error('Failed to start:', error);
    }
  }
  
  // Start when page loads
  // start();
  */
}
