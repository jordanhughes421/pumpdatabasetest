import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { redeemInvite } from '../api/client';

const InviteRedeem: React.FC = () => {
    const { token } = useParams<{ token: string }>();
    const navigate = useNavigate();
    const { token: authToken } = useAuth(); // Check if logged in

    useEffect(() => {
        const redeem = async () => {
            if (!token) return;

            if (!authToken) {
                // Store invite token and redirect to login/register?
                // For MVP, just redirect to login with a query param
                // Or force login first.
                navigate(`/login?redirect=/invite/${token}`);
                return;
            }

            try {
                await redeemInvite(token);
                alert('Invite redeemed successfully! You are now a member.');
                // Refresh auth state? Ideally yes. For MVP, reload page or redirect home.
                window.location.href = '/';
            } catch (err: any) {
                alert(`Failed to redeem invite: ${err.response?.data?.detail || err.message}`);
                navigate('/');
            }
        };
        redeem();
    }, [token, authToken, navigate]);

    return (
        <div className="flex justify-center items-center h-screen">
            <p>Redeeming invite...</p>
        </div>
    );
};

export default InviteRedeem;
