import { NextRequest, NextResponse } from "next/server";
const api=process.env.BREERO_API_INTERNAL_URL??process.env.NEXT_PUBLIC_API_URL??"https://api.breero.com/api/v1";
export async function POST(request:NextRequest){
  const form=await request.formData(); const checked=(name:string)=>form.get(name)==="on";
  const response=await fetch(`${api}/communications/preferences`,{method:"POST",headers:{"content-type":"application/json","user-agent":request.headers.get("user-agent")??"","x-forwarded-for":request.headers.get("x-forwarded-for")??""},body:JSON.stringify({destination:form.get("destination"),transactionalEmail:checked("transactionalEmail"),transactionalSms:checked("transactionalSms"),marketingEmail:checked("marketingEmail"),marketingSms:checked("marketingSms"),source_url:new URL("/communications-preferences",request.url).toString(),disclosure_text:"I choose the separately listed BREERO communication purposes. Marketing is not required for service and is currently disabled.",policy_versions:{communications:"2026.08.13",privacy:"2026.08.13",sms:"2026.08.13"}}),cache:"no-store"});
  const body=await response.json(); return NextResponse.json(body,{status:response.status});
}
