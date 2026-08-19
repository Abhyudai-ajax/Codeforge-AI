'use client';
import React from 'react';import Sidebar from './Sidebar';import Header from './Header';
export default function MainLayout({children,title,onSearch}:{children:React.ReactNode;title?:string;onSearch?:(q:string)=>void}){return <div className="flex h-screen overflow-hidden bg-gray-950"><Sidebar/><div className="min-w-0 flex-1 flex flex-col"><Header title={title} onSearch={onSearch}/><main className="min-h-0 flex-1 overflow-auto">{children}</main></div></div>}
