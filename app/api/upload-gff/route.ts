import { type HandleUploadBody, handleUpload } from "@vercel/blob/client";
import { NextResponse } from "next/server";

export async function POST(request: Request): Promise<NextResponse> {
  const body = (await request.json()) as HandleUploadBody;

  try {
    const jsonResponse = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async (pathname) => {
        // トークン生成前の認証/認可処理
        // 実際のアプリでは、ここでユーザー認証を行うべきです

        return {
          allowedContentTypes: ["application/gff3", "text/plain"],
          tokenPayload: JSON.stringify({
            // オプション：アップロード完了時にサーバーに送信される情報
          }),
        };
      },
      onUploadCompleted: async ({ blob, tokenPayload }) => {
        // アップロード完了時の処理
        // ローカル環境ではこの処理は実行されないため、
        // ngrokなどのトンネリングサービスを使用してテストすることをお勧めします

        console.log("GFFファイルのアップロードが完了しました", blob);

        try {
          // アップロード完了後の処理をここに記述
          // 例：データベースの更新など
        } catch (error) {
          throw new Error("アップロード後の処理に失敗しました");
        }
      },
    });

    return NextResponse.json(jsonResponse);
  } catch (error) {
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 400 },
    );
  }
}
