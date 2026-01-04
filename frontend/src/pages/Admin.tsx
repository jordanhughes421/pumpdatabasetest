import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getMembers, createInvite, updateMemberRole, removeMember } from '../api/client';
import { useAuth } from '../context/AuthContext';

const Admin: React.FC = () => {
    const { activeOrg, role } = useAuth();
    const queryClient = useQueryClient();
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteRole, setInviteRole] = useState('viewer');
    const [inviteLink, setInviteLink] = useState('');

    if (role !== 'admin' || !activeOrg) {
        return <div>Access Denied</div>;
    }

    const { data: members, isLoading } = useQuery({
        queryKey: ['members', activeOrg.id],
        queryFn: () => getMembers(activeOrg.id)
    });

    const inviteMutation = useMutation({
        mutationFn: (data: { email: string, role: string }) => createInvite(activeOrg.id, data.email, data.role),
        onSuccess: (data) => {
            setInviteLink(`${window.location.origin}/invite/${data.invite_token}`);
            alert(`Invite created! Link: ${window.location.origin}/invite/${data.invite_token}`);
        }
    });

    const updateRoleMutation = useMutation({
        mutationFn: (data: { userId: number, role: string }) => updateMemberRole(activeOrg.id, data.userId, data.role),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['members'] })
    });

    const removeMemberMutation = useMutation({
        mutationFn: (userId: number) => removeMember(activeOrg.id, userId),
        onSuccess: () => queryClient.invalidateQueries({ queryKey: ['members'] })
    });

    return (
        <div className="container mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">Organization Administration: {activeOrg.name}</h1>

            <div className="bg-white p-6 rounded shadow mb-6">
                <h2 className="text-xl font-semibold mb-4">Invite New Member</h2>
                <div className="flex gap-4">
                    <input
                        type="email"
                        placeholder="Email"
                        className="border p-2 rounded flex-1"
                        value={inviteEmail}
                        onChange={e => setInviteEmail(e.target.value)}
                    />
                    <select
                        className="border p-2 rounded"
                        value={inviteRole}
                        onChange={e => setInviteRole(e.target.value)}
                    >
                        <option value="viewer">Viewer</option>
                        <option value="editor">Editor</option>
                        <option value="admin">Admin</option>
                    </select>
                    <button
                        className="bg-blue-600 text-white px-4 py-2 rounded"
                        onClick={() => inviteMutation.mutate({ email: inviteEmail, role: inviteRole })}
                    >
                        Generate Invite Link
                    </button>
                </div>
                {inviteLink && (
                    <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded text-green-800 break-all">
                        <strong>Invite Link:</strong> {inviteLink}
                    </div>
                )}
            </div>

            <div className="bg-white p-6 rounded shadow">
                <h2 className="text-xl font-semibold mb-4">Members</h2>
                {isLoading ? <p>Loading...</p> : (
                    <table className="min-w-full">
                        <thead>
                            <tr className="bg-gray-50">
                                <th className="text-left p-3">User</th>
                                <th className="text-left p-3">Role</th>
                                <th className="text-right p-3">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {members?.map((m: any) => (
                                <tr key={m.id} className="border-t">
                                    <td className="p-3">
                                        <div>{m.user.email}</div>
                                        <div className="text-xs text-gray-500">{m.user.is_active ? 'Active' : 'Inactive'}</div>
                                    </td>
                                    <td className="p-3">
                                        <select
                                            value={m.role}
                                            onChange={(e) => updateRoleMutation.mutate({ userId: m.user.id, role: e.target.value })}
                                            className="border rounded p-1"
                                        >
                                            <option value="viewer">Viewer</option>
                                            <option value="editor">Editor</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    </td>
                                    <td className="p-3 text-right">
                                        <button
                                            className="text-red-600 hover:text-red-800"
                                            onClick={() => {
                                                if(confirm('Remove this user?')) removeMemberMutation.mutate(m.user.id);
                                            }}
                                        >
                                            Remove
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>
        </div>
    );
};

export default Admin;
