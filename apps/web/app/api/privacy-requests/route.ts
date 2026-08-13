import { NextRequest, NextResponse } from "next/server";
const api=process.env.BREERO_API_INTERNAL_URL??process.env.NEXT_PUBLIC_API_URL??"https://api.breero.com/api/v1";
export async function POST(request:NextRequest){
  const form=await request.formData();
  const response=await fetch(`${api}/privacy-requests`,{method:"POST",headers:{"content-type":"application/json","user-agent":request.headers.get("user-agent")??"","x-forwarded-for":request.headers.get("x-forwarded-for")??""},body:JSON.stringify({requestType:form.get("requestType"),email:form.get("email"),gpc:request.headers.get("sec-gpc")==="1"}),cache:"no-store"});
  const body=await response.json(); return NextResponse.json(body,{status:response.status});
}
