// src/modules/Auth/components/LoginForm.jsx
import React, { useState } from 'react';
import { authApi } from '../api';

export default function LoginForm({ onSuccess }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({ phone: '', api_id: '', api_hash: '', code: '' });
  const [hash, setHash] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRequestCode = async () => {
    setLoading(true);
    try {
      const res = await authApi.requestCode({
        phone: formData.phone,
        api_id: formData.api_id,
        api_hash: formData.api_hash
      });
      setHash(res.data.phone_code_hash);
      setStep(2);
    } catch (err) {
      alert("Error requesting code. Check console.");
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setLoading(true);
    try {
      await authApi.verifyCode({
        phone: formData.phone,
        code: formData.code,
        phone_code_hash: hash
      });
      alert("Agent Added Successfully!");
      if (onSuccess) onSuccess();
    } catch (err) {
      alert("Verification Failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      {step === 1 ? (
        <div>
          <div className="input-group">
            <label className="input-label">Phone Number</label>
            <input
              className="input-field"
              placeholder="+98..."
              value={formData.phone}
              onChange={e => setFormData({ ...formData, phone: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label className="input-label">API ID</label>
            <input
              className="input-field"
              placeholder="API ID"
              value={formData.api_id}
              onChange={e => setFormData({ ...formData, api_id: e.target.value })}
            />
          </div>
          <div className="input-group">
            <label className="input-label">API Hash</label>
            <input
              className="input-field"
              placeholder="API Hash"
              value={formData.api_hash}
              onChange={e => setFormData({ ...formData, api_hash: e.target.value })}
            />
          </div>
          <button disabled={loading} className="btn-primary" style={{ width: '100%' }} onClick={handleRequestCode}>
            {loading ? 'Sending...' : 'Send Code'}
          </button>
        </div>
      ) : (
        <div>
          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 0 }}>Code sent to {formData.phone}</p>
          <div className="input-group">
            <label className="input-label">Telegram Code</label>
            <input
              className="input-field"
              placeholder="12345"
              value={formData.code}
              onChange={e => setFormData({ ...formData, code: e.target.value })}
            />
          </div>
          <button disabled={loading} className="btn-primary" style={{ width: '100%' }} onClick={handleVerify}>
            {loading ? 'Verifying...' : 'Verify & Login'}
          </button>
        </div>
      )}
    </div>
  );
}