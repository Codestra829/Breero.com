import { Button, EmptyState } from "@breero/ui";
export default function AccountNotFound(){return <EmptyState title="We couldn’t find that" description="It may have been removed, or it may belong to a different account." action={<Button variant="outline">Back to my account</Button>}/>}
